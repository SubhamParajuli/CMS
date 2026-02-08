from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
#Create custom user model for the canteen management system

class CustomUser(AbstractUser):

    user_code = models.CharField(max_length=5, unique=True)
    Role_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    role = models.CharField(max_length=20, choices=Role_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"


