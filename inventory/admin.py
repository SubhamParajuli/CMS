from django.contrib import admin
from .models import Inventory
# Register your models here.


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'category', 'price','food_image', 'quantity', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('item_name',)