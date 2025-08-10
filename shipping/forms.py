from django import forms
from .models import ShippingAddress


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = [
            'full_name', 'address_line_1', 'address_line_2', 
            'city', 'state', 'postal_code', 'country', 
            'phone_number', 'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address, P.O. box, company name'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, suite, unit, building, floor, etc.'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province/Region'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP/Postal code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address_line_2'].required = False
        self.fields['phone_number'].required = False
        
        # Add help text
        self.fields['is_default'].help_text = 'Set as default shipping address'
        
    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code:
            # Remove spaces and convert to uppercase
            postal_code = postal_code.replace(' ', '').upper()
        return postal_code
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove all non-digit characters except +
            import re
            phone_number = re.sub(r'[^\d+]', '', phone_number)
        return phone_number


class ShippingCalculatorForm(forms.Form):
    """Form for shipping cost calculation"""
    weight = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Weight in kg',
            'step': '0.1',
            'min': '0.1'
        }),
        help_text='Enter the total weight of your package in kilograms'
    )
    
    destination_country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Destination country'
        }),
        help_text='Enter the destination country'
    )
    
    destination_city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Destination city (optional)'
        }),
        help_text='Enter the destination city for more accurate estimates'
    )
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight and weight <= 0:
            raise forms.ValidationError('Weight must be greater than 0')
        return weight


class TrackingForm(forms.Form):
    """Form for tracking order by tracking number"""
    tracking_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tracking number',
            'style': 'text-transform: uppercase;'
        }),
        help_text='Enter your tracking number to get shipment status'
    )
    
    def clean_tracking_number(self):
        tracking_number = self.cleaned_data.get('tracking_number')
        if tracking_number:
            # Convert to uppercase and remove spaces
            tracking_number = tracking_number.upper().replace(' ', '')
        return tracking_number
