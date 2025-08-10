from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Review listing and filtering
    path('', views.review_list, name='review_list'),
    path('product/<int:product_id>/', views.product_reviews, name='product_reviews'),
    
    # Review creation and management
    path('add/<int:product_id>/', views.add_review, name='add_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    # Review interaction
    path('helpful/<int:review_id>/', views.mark_helpful, name='mark_helpful'),
    path('report/<int:review_id>/', views.report_review, name='report_review'),
    
    # AJAX endpoints
    path('ajax/add/', views.ajax_add_review, name='ajax_add_review'),
    path('ajax/helpful/<int:review_id>/', views.ajax_mark_helpful, name='ajax_mark_helpful'),
    
    # Review management for users
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('pending/', views.pending_reviews, name='pending_reviews'),
]
