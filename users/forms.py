from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django import forms

COUNTRY_CHOICES = [
    ('', 'Select Country'),
    ('KE', 'Kenya'),
    ('TZ', 'Tanzania'),
    ('UG', 'Uganda'),
    ('RW', 'Rwanda'),
    ('NG', 'Nigeria'),
    ('GH', 'Ghana'),
    # Add more countries as needed
]

class PhoneEmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Phone number or Email",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Phone number or Email"})
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Try to authenticate by email
            try:
                user_obj = User.objects.get(email=username)
                if user_obj.check_password(password):
                    self.confirm_login_allowed(user_obj)
                    self.user_cache = user_obj
                    return self.cleaned_data
            except User.DoesNotExist:
                pass
            
            # Try to authenticate by phone (from UserProfile)
            try:
                profile = UserProfile.objects.get(phone=username)
                user_obj = profile.user
                if user_obj.check_password(password):
                    self.confirm_login_allowed(user_obj)
                    self.user_cache = user_obj
                    return self.cleaned_data
            except UserProfile.DoesNotExist:
                pass
        
        # If we get here, authentication failed
        return super().clean()

    def get_user(self):
        return getattr(self, 'user_cache', None)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "country", "password1", "password2")

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) < 8:
            raise forms.ValidationError("Phone number is too short.")
        if UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Phone number already registered.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                address='',
                avatar=None,
                country=self.cleaned_data['country']
            )
        return user
