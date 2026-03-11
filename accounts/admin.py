from django.contrib import admin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username','user_code','role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff')
    search_fields = ('username','user_code')
