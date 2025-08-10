from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Review
from products.models import Product


def review_list(request):
    """List all reviews"""
    reviews = Review.objects.filter(is_approved=True).order_by('-created_at')
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reviews': page_obj.object_list,
    }
    return render(request, 'reviews/review_list.html', context)


def product_reviews(request, product_id):
    """List reviews for a specific product"""
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product, is_approved=True).order_by('-created_at')
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    return render(request, 'reviews/product_reviews.html', context)


@login_required
def add_review(request, product_id):
    """Add a review for a product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Basic review creation logic
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            try:
                Review.objects.create(
                    user=request.user,
                    product=product,
                    rating=int(rating),
                    comment=comment
                )
                messages.success(request, 'Review submitted successfully!')
                return redirect('products:product_detail', pk=product.id)
            except Exception as e:
                messages.error(request, 'Error submitting review.')
    
    context = {'product': product}
    return render(request, 'reviews/add_review.html', context)


@login_required
def edit_review(request, review_id):
    """Edit a review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            review.rating = int(rating)
            review.comment = comment
            review.save()
            messages.success(request, 'Review updated successfully!')
            return redirect('reviews:my_reviews')
    
    context = {'review': review}
    return render(request, 'reviews/edit_review.html', context)


@login_required
def delete_review(request, review_id):
    """Delete a review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('reviews:my_reviews')
    
    context = {'review': review}
    return render(request, 'reviews/delete_review.html', context)


@login_required
@require_POST
def mark_helpful(request, review_id):
    """Mark a review as helpful"""
    review = get_object_or_404(Review, id=review_id)
    # Basic implementation
    review.helpful_count += 1
    review.save()
    
    return JsonResponse({'success': True, 'helpful_count': review.helpful_count})


@login_required
@require_POST
def report_review(request, review_id):
    """Report a review"""
    review = get_object_or_404(Review, id=review_id)
    # Basic implementation
    messages.info(request, 'Review reported. Thank you for your feedback.')
    return redirect('reviews:product_reviews', product_id=review.product.id)


@login_required
@require_POST
def ajax_add_review(request):
    """AJAX endpoint for adding reviews"""
    product_id = request.POST.get('product_id')
    rating = request.POST.get('rating')
    comment = request.POST.get('comment')
    
    if not all([product_id, rating, comment]):
        return JsonResponse({'success': False, 'message': 'Missing required fields'})
    
    try:
        product = Product.objects.get(id=product_id)
        review = Review.objects.create(
            user=request.user,
            product=product,
            rating=int(rating),
            comment=comment
        )
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully!',
            'review_id': review.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error submitting review'})


@login_required
@require_POST
def ajax_mark_helpful(request, review_id):
    """AJAX endpoint for marking reviews helpful"""
    try:
        review = Review.objects.get(id=review_id)
        review.helpful_count += 1
        review.save()
        return JsonResponse({'success': True, 'helpful_count': review.helpful_count})
    except Review.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Review not found'})


@login_required
def my_reviews(request):
    """List user's reviews"""
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    
    context = {'reviews': reviews}
    return render(request, 'reviews/my_reviews.html', context)


@login_required
def pending_reviews(request):
    """List pending reviews (admin only)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    reviews = Review.objects.filter(is_approved=False).order_by('-created_at')
    
    context = {'reviews': reviews}
    return render(request, 'reviews/pending_reviews.html', context)
