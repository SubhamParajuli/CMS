import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from inventory.models import Inventory
from orders.models import Order, OrderItem
from payments.models import Payment, Receipt


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class CheckoutTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='checkout_user',
            password='testpass123',
            user_code='45678',
            role='student',
        )
        self.item_one = Inventory.objects.create(
            item_name='Tea',
            category='beverages',
            price='25.00',
            quantity=5,
            is_available=True,
        )
        self.item_two = Inventory.objects.create(
            item_name='Momo',
            category='snacks',
            price='120.00',
            quantity=2,
            is_available=True,
        )
        self.client.force_login(self.user)

    def post_checkout(self, cart):
        return self.client.post(
            reverse('checkout'),
            data=json.dumps({'cart': cart}),
            content_type='application/json',
        )

    def test_checkout_rejects_negative_quantity(self):
        response = self.post_checkout({
            str(self.item_one.id): {'quantity': -1},
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'],
            'Quantity must be at least 1 for every item',
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(Receipt.objects.count(), 0)

        self.item_one.refresh_from_db()
        self.assertEqual(self.item_one.quantity, 5)

    def test_checkout_rolls_back_if_any_item_exceeds_stock(self):
        response = self.post_checkout({
            str(self.item_one.id): {'quantity': 2},
            str(self.item_two.id): {'quantity': 3},
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Only 2 left for Momo')
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(Receipt.objects.count(), 0)

        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        self.assertEqual(self.item_one.quantity, 5)
        self.assertEqual(self.item_two.quantity, 2)
        self.assertTrue(self.item_one.is_available)
        self.assertTrue(self.item_two.is_available)

    def test_checkout_creates_order_payment_and_receipt(self):
        response = self.post_checkout({
            str(self.item_one.id): {'quantity': 2},
            str(self.item_two.id): {'quantity': 2},
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_amount, Decimal('290.00'))
        self.assertTrue(order.is_paid)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 2)

        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.amount_paid, Decimal('290.00'))
        self.assertTrue(Receipt.objects.filter(order=order).exists())

        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        self.assertEqual(self.item_one.quantity, 3)
        self.assertEqual(self.item_two.quantity, 0)
        self.assertFalse(self.item_two.is_available)

    def test_checkout_rolls_back_if_payment_creation_fails(self):
        with patch('orders.views.Payment.objects.create', side_effect=RuntimeError('payment failed')):
            with self.assertRaises(RuntimeError):
                self.post_checkout({
                    str(self.item_one.id): {'quantity': 2},
                })

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(Receipt.objects.count(), 0)

        self.item_one.refresh_from_db()
        self.assertEqual(self.item_one.quantity, 5)
        self.assertTrue(self.item_one.is_available)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class CheckoutAuthRedirectTests(TestCase):
    def test_checkout_redirects_anonymous_user_to_login(self):
        response = self.client.post(
            reverse('checkout'),
            data=json.dumps({'cart': {}}),
            content_type='application/json',
        )

        self.assertRedirects(response, '/login/?next=/checkout/')
