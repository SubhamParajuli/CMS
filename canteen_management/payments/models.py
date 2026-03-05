from django.db import models
from orders.models import *

# Create your models here.
class Payment(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE
    )

    payment_method = models.CharField(
        max_length=10,
        default='CASH'
    )

    amount_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    payment_time = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Payment for Order #{self.order.id}"


class Receipt(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Receipt for Order #{self.order.id}"

