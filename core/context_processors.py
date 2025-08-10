from products.models import Category
from django.conf import settings

def global_context(request):
    # Provide categories and currencies to all templates
    return {
        'categories': Category.objects.all(),
        'currencies': getattr(settings, 'CURRENCIES', []),
        'current_currency': request.session.get('currency', settings.DEFAULT_CURRENCY),
    }
