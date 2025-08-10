from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import re

from .models import Store, StoreApplication, StoreReview
from products.models import Product, Category, Brand


class StoreApplicationForm(forms.ModelForm):
    """Form for applying to become a seller"""
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the terms and conditions for sellers"
    )
    
    class Meta:
        model = StoreApplication
        fields = [
            'store_name', 'store_description', 'business_type',
            'business_license', 'tax_id', 'contact_email', 'contact_phone',
            'business_address', 'license_document', 'tax_document', 'identity_document'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your store name'
            }),
            'store_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your store and what you plan to sell'
            }),
            'business_type': forms.Select(attrs={'class': 'form-control'}),
            'business_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business license number (if applicable)'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax identification number (if applicable)'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact email address'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact phone number'
            }),
            'business_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your complete business address'
            }),
            'license_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'tax_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'identity_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
    
    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if phone:
            # Remove any non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            
            # Validate Kenyan phone number format
            if not (phone_digits.startswith('254') or phone_digits.startswith('0')):
                raise ValidationError('Please enter a valid Kenyan phone number')
            
            # Normalize to international format
            if phone_digits.startswith('0'):
                phone_digits = '254' + phone_digits[1:]
            
            if len(phone_digits) != 12:
                raise ValidationError('Phone number must be 12 digits (including country code)')
            
            return '+' + phone_digits
        return phone
    
    def clean_store_name(self):
        name = self.cleaned_data.get('store_name')
        if name:
            # Check if store name already exists
            if StoreApplication.objects.filter(store_name__iexact=name).exists():
                raise ValidationError('A store application with this name already exists')
            if Store.objects.filter(name__iexact=name).exists():
                raise ValidationError('A store with this name already exists')
        return name


class StoreForm(forms.ModelForm):
    """Form for editing store settings"""
    
    class Meta:
        model = Store
        fields = [
            'name', 'description', 'short_description', 'logo', 'banner', 'phone', 'email',
            'address', 'city', 'state', 'country', 'postal_code', 'website', 'facebook',
            'instagram', 'twitter', 'return_policy', 'shipping_policy', 'store_type'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Store name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Store description'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short description (500 chars max)'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Store email'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Store address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Region'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://your-website.com'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Facebook page URL'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Instagram profile URL'
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Twitter profile URL'
            }),
            'return_policy': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your return policy'
            }),
            'shipping_policy': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your shipping policy'
            }),
            'store_type': forms.Select(attrs={'class': 'form-control'}),
        }


class ProductForm(forms.ModelForm):
    """Form for adding/editing products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'brand', 'sku',
            'price', 'stock', 'weight', 'image', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Product description'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU (Stock Keeping Unit)'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Price in KES'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Stock quantity'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Weight in kg'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty option for brand
        self.fields['brand'].empty_label = "Select Brand (Optional)"
        
        # Set default values
        if not self.instance.pk:
            self.fields['is_active'].initial = True


class StoreReviewForm(forms.ModelForm):
    """Form for store reviews"""
    
    class Meta:
        model = StoreReview
        fields = ['rating', 'title', 'review']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Review title'
            }),
            'review': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this store'
            }),
        }
