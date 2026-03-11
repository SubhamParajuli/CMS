
# Create your views here.

from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
import json
from .models import Inventory
from django.contrib.auth.decorators import login_required


@login_required
def inventory_list(request):
    items = Inventory.objects.filter(is_available=True, quantity__gt=0)
    context = {'inventory': items}
    return render(request, 'menu.html', context)
