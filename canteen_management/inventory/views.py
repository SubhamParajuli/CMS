
# Create your views here.

from django.shortcuts import render, redirect
from .models import Inventory
from django.contrib.auth.decorators import login_required


@login_required
def inventory_list(request):
    items = Inventory.objects.filter(is_available = True)
    context = {'items': items}
    return render(request, 'menu.html', context)


@login_required
def add_to_cart(request,item_id):
    item = Inventory.objects.get(id=item_id)
    cart = request.session.get('cart', {})
    cart[item_id] = cart.get(item_id, 0) + 1
    request.session['cart'] = cart
    return redirect('inventory_list')   
        
