from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from inventory.models import Inventory
from .models import *
from django.contrib import messages
from payments.models import *

# Create your views here.
