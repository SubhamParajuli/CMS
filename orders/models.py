from django.db import models
from django.conf import settings
from inventory.models import Inventory

# Create your models here.

class Order(models.Model):
    user=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    order_date=models.DateTimeField(auto_now_add=True)
    total_amount=models.DecimalField(
        max_digits=8,
        decimal_places=2
    )
    is_paid=models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    item = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.item.item_name} x {self.quantity}"