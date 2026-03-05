from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import Order
from .models import Receipt


@login_required
def receipt_view(request, order_id):

    order = get_object_or_404(Order, id=order_id, user=request.user)

    receipt, created = Receipt.objects.get_or_create(order=order)

    return render(request, "receipt.html", {
        "order": order,
        "receipt": receipt
    })