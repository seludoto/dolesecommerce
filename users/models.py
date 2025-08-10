from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    country = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True, help_text="Tell us about yourself")
    is_public = models.BooleanField(default=False, help_text="Make profile visible in user registry")
    is_verified = models.BooleanField(default=False, help_text="Verified user badge")
    date_of_birth = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def display_name(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username
