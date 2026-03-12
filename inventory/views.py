from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import Inventory


def _serialize_inventory_item(item):
    return {
        'id': item.id,
        'item_name': item.item_name,
        'category': item.category,
        'category_label': item.get_category_display(),
        'price': str(item.price),
        'quantity': item.quantity,
        'is_available': item.is_available,
        'food_image_url': item.food_image.url if item.food_image else '',
    }


@login_required
def inventory_list(request):
    items = Inventory.objects.filter(is_available=True, quantity__gt=0)
    context = {'inventory': items}
    return render(request, 'menu.html', context)


@login_required
def inventory_snapshot(request):
    items = Inventory.objects.filter(is_available=True, quantity__gt=0).order_by('item_name', 'id')
    return JsonResponse(
        {
            'items': [_serialize_inventory_item(item) for item in items],
            'generated_at': request.headers.get('X-Request-Id', ''),
        }
    )
