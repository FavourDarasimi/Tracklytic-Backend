from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField()
    phone_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'  # Use email for authentication
    REQUIRED_FIELDS = ['username','phone_number','age']  # Username still required for compatibility

    def __str__(self):
        return self.email
#day2

# Create your models here.
