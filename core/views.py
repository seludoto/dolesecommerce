from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect

# Currency switcher view
@require_POST
@csrf_exempt
def set_currency(request):
    currency = request.POST.get('currency')
    next_url = request.POST.get('next', '/')
    valid_currencies = [c[0] for c in getattr(settings, 'CURRENCIES', [])]
    if currency in valid_currencies:
        request.session['currency'] = currency
    return redirect(next_url)
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q
from products.models import Product
from users.models import UserProfile
from reviews.models import Review
from orders.models import Order


def home(request):
    products = Product.objects.filter(is_active=True)[:3]
    return render(request, 'core/home.html', {'products': products})


def deals_view(request):
    # Add some context for deals template
    context = {
        'total_deals': '150+',
        'total_savings': '$50K+',
        'happy_customers': '2.5K+',
        'avg_discount': '45%',
    }
    return render(request, 'core/deals.html', context)


def registry_view(request):
    # Get public profiles for the registry
    search_query = request.GET.get('search', '')
    public_profiles = UserProfile.objects.filter(is_public=True).select_related('user')
    
    if search_query:
        public_profiles = public_profiles.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    # Get statistics for the page
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__isnull=False).count()
    total_reviews = Review.objects.count() if hasattr(Review, 'objects') else 0
    verified_buyers = UserProfile.objects.filter(is_verified=True).count()
    
    context = {
        'public_profiles': public_profiles[:20],  # Limit to 20 profiles
        'total_users': total_users,
        'active_users': active_users,
        'total_reviews': total_reviews,
        'verified_buyers': verified_buyers,
    }
    return render(request, 'core/registry.html', context)


def customer_service_view(request):
    return render(request, 'core/customer_service.html')


def help_view(request):
    """Help center page"""
    faq_items = [
        {
            'question': 'How do I place an order?',
            'answer': 'Browse our products, add items to your cart, and proceed to checkout. You can pay using various secure payment methods.'
        },
        {
            'question': 'What payment methods do you accept?',
            'answer': 'We accept major credit cards, PayPal, mobile money, and bank transfers.'
        },
        {
            'question': 'How can I track my order?',
            'answer': 'Go to your dashboard and click on "Order History" to view all your orders and their current status.'
        },
        {
            'question': 'What is your return policy?',
            'answer': 'We offer a 30-day return policy for most items. Items must be in original condition.'
        },
        {
            'question': 'How do I use coupon codes?',
            'answer': 'Enter your coupon code at checkout or apply it in your shopping cart before proceeding to payment.'
        }
    ]
    
    context = {
        'faq_items': faq_items,
    }
    return render(request, 'core/help.html', context)


def debug_static_view(request):
    """Debug static files - useful for development"""
    from django.conf import settings
    context = {
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'debug': settings.DEBUG,
    }
    return render(request, 'debug_static.html', context)


def terms_view(request):
    """Terms and Conditions page"""
    return render(request, 'core/terms.html')


def privacy_view(request):
    """Privacy Policy page"""
    return render(request, 'core/privacy.html')
