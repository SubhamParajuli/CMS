import json
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from inventory.models import Inventory
from .models import Order, OrderItem
from payments.models import Payment, Receipt


class CheckoutValidationError(Exception):
    pass


def _normalize_cart(cart):
    if not isinstance(cart, dict) or not cart:
        raise CheckoutValidationError("Cart is empty")

    normalized_cart = {}

    for raw_item_id, item_data in cart.items():
        if not isinstance(item_data, dict):
            raise CheckoutValidationError("Invalid cart data")

        try:
            item_id = int(raw_item_id)
            quantity = int(item_data.get("quantity"))
        except (TypeError, ValueError):
            raise CheckoutValidationError("Invalid quantity provided")

        if quantity < 1:
            raise CheckoutValidationError("Quantity must be at least 1 for every item")

        normalized_cart[item_id] = quantity

    return normalized_cart


def _validate_inventory(normalized_cart):
    inventory_items = {
        item.id: item
        for item in Inventory.objects.select_for_update().filter(id__in=normalized_cart.keys())
    }
    validated_items = []

    for item_id, quantity in normalized_cart.items():
        inventory_item = inventory_items.get(item_id)

        if inventory_item is None:
            raise CheckoutValidationError("One or more items are no longer available")

        if not inventory_item.is_available or inventory_item.quantity < 1:
            raise CheckoutValidationError(f"{inventory_item.item_name} is not available right now")

        if inventory_item.quantity < quantity:
            raise CheckoutValidationError(
                f"Only {inventory_item.quantity} left for {inventory_item.item_name}"
            )

        validated_items.append((inventory_item, quantity))

    return validated_items


@login_required
@require_POST
def checkout(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request payload"}, status=400)

    try:
        normalized_cart = _normalize_cart(data.get("cart", {}))

        with transaction.atomic():
            validated_items = _validate_inventory(normalized_cart)

            total_amount = Decimal("0.00")
            for inventory_item, quantity in validated_items:
                total_amount += inventory_item.price * quantity

            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
            )

            for inventory_item, quantity in validated_items:
                price = inventory_item.price

                OrderItem.objects.create(
                    order=order,
                    item=inventory_item,
                    quantity=quantity,
                    price_at_purchase=price,
                )

                inventory_item.quantity -= quantity
                if inventory_item.quantity == 0:
                    inventory_item.is_available = False
                inventory_item.save(update_fields=["quantity", "is_available"])
            Payment.objects.create(
                order=order,
                payment_method="CASH",
                amount_paid=total_amount,
            )
            Receipt.objects.create(order=order)
            order.is_paid = True
            order.save(update_fields=["is_paid"])
    except CheckoutValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({
        "success": True,
        "order_id": order.id
    })
