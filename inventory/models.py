from django.db import models

# Create your models here.

class Inventory(models.Model):
    item_name=models.CharField(max_length=100)
    category= models.CharField(max_length=50, choices=(
        ('main_course', 'Main Course'),
        ('snacks', 'Snacks'),
        ('beverages', 'Beverages'),
        ('desserts', 'Desserts'),
        ('other', 'Other'),
    ))
    price=models.DecimalField(max_digits=6,decimal_places=2)
    quantity=models.PositiveIntegerField()
    food_image=models.ImageField(upload_to='inventory_images/', null=True, blank=True)
    is_available=models.BooleanField(default=True)

    def __str__(self):
        return f"{self.item_name} ({self.quantity})"