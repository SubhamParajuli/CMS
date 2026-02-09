
# Create your views here.

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Inventory
from django.contrib.auth.decorators import login_required


@login_required
def inventory_list(request):
    items = Inventory.objects.filter(is_available = True)
    context = {'inventory': items}
    return render(request, 'menu.html', context)



def payment_page(request):
    return HttpResponse("Payment Page")