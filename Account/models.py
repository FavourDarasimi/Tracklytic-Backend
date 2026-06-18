from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from cloudinary.models import CloudinaryField


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'  # Use email for authentication
    REQUIRED_FIELDS = ['username']  # Username still required for compatibility

    def __str__(self):
        return self.email


CURRENCIES = [
    ("NGN", "Naira (NGN)"),
    ("USD", "US Dollar (USD)"),
    ("EUR", "Euro (EUR)"),
    ("GBP", "British Pound (GBP)"),
    ("CAD", "Canadian Dollar (CAD)"),
    ("AUD", "Australian Dollar (AUD)"),
    ("JPY", "Japanese Yen (JPY)"),
    ("KES", "Kenyan Shilling (KES)"),
    ("ZAR", "South African Rand (ZAR)"),
    ("GHS", "Ghanaian Cedi (GHS)"),
]

TIMEZONE_CHOICES = [(tz, tz) for tz in [
    "UTC", "Africa/Lagos", "Africa/Nairobi", "Africa/Johannesburg",
    "Africa/Accra", "Africa/Cairo", "Europe/London", "Europe/Paris",
    "Europe/Berlin", "America/New_York", "America/Chicago",
    "America/Denver", "America/Los_Angeles", "Asia/Dubai",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata",
]]

LOCALE_CHOICES = [
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("de", "German"),
    ("pt", "Portuguese"),
    ("ar", "Arabic"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
]


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = CloudinaryField("avatars/", blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=True)
    locale = models.CharField(max_length=10, choices=LOCALE_CHOICES, default="en")
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default="UTC")
    base_currency = models.CharField(
        max_length=3, choices=CURRENCIES, default="NGN"
    )
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} profile"


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
