from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import Order
from .models import Payment, Receipt


@login_required
def receipt_view(request, order_id):

    order = get_object_or_404(Order, id=order_id, user=request.user, is_paid=True)
    payment = get_object_or_404(Payment, order=order)
    receipt = get_object_or_404(Receipt, order=order)

    return render(request, "receipt.html", {
        "order": order,
        "payment": payment,
        "receipt": receipt
    })
