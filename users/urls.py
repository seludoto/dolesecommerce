from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Dashboard & Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('update-profile/', views.update_profile, name='update_profile'),
    
    # Settings
    path('privacy-settings/', views.privacy_settings_view, name='privacy_settings'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # KiKUU-style Features
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('saved-for-later/', views.saved_for_later_view, name='saved_for_later'),
    path('coupons/', views.coupons_view, name='coupons'),
    path('addresses/', views.addresses_view, name='addresses'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('invite-friends/', views.invite_friends_view, name='invite_friends'),
]
