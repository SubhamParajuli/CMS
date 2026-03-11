import re

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models


ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('student', 'Student'),
    ('teacher', 'Teacher'),
)

ROLE_VALUES = [choice for choice, _ in ROLE_CHOICES]

class CustomUserManager(UserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        role = extra_fields.get('role')
        valid_roles = self.model.valid_roles()

        if role not in valid_roles:
            raise ValueError('A valid role is required.')

        if role == 'admin':
            extra_fields.setdefault('is_staff', True)

        return super().create_user(username, email=email, password=password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('role') != 'admin':
            raise ValueError('Superusers must use the admin role.')

        return super().create_superuser(username, email=email, password=password, **extra_fields)


# Create your models here.
#Create custom user model for the canteen management system

class CustomUser(AbstractUser):
    REQUIRED_FIELDS = ['user_code']

    user_code = models.CharField(max_length=5, unique=True)
    ROLE_CHOICES = ROLE_CHOICES
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    objects = CustomUserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(role__in=ROLE_VALUES),
                name='accounts_customuser_valid_role',
            ),
        ]

    @classmethod
    def valid_roles(cls):
        return {choice for choice, _ in cls.ROLE_CHOICES}

    @classmethod
    def registration_roles(cls):
        return {'student', 'teacher'}

    @classmethod
    def is_valid_user_code(cls, user_code):
        return bool(re.fullmatch(r'^\d{5}$', user_code or ''))

    @property
    def is_canteen_admin(self):
        return self.is_superuser or self.role == 'admin'

    def clean(self):
        super().clean()

        if self.role not in self.valid_roles():
            raise ValidationError({'role': 'Select a valid role.'})

        if not self.is_valid_user_code(self.user_code):
            raise ValidationError({'user_code': 'User code must be exactly 5 digits.'})

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and set(update_fields) == {'last_login'}:
            return super().save(*args, **kwargs)

        if not self.role and (self.is_staff or self.is_superuser):
            self.role = 'admin'

        if self.is_superuser:
            self.role = 'admin'

        self.is_staff = self.is_superuser or self.role == 'admin'
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
