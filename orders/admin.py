from django.contrib import admin
from .models import Order, OrderItem

# Register your models here.

class OrderItemInline(admin.TabularInline):
    model=OrderItem
    extra=0
    readonly_fields = ('item', 'quantity', 'price_at_purchase')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'order_date')
    inlines = [OrderItemInline]  
