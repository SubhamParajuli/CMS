from io import StringIO
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from orders.models import Order
from payments.models import Payment, Receipt


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class ReceiptViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='receipt_user',
            password='testpass123',
            user_code='56789',
            role='student',
        )
        self.client.force_login(self.user)

    def test_receipt_view_returns_404_when_payment_or_receipt_is_missing(self):
        order = Order.objects.create(
            user=self.user,
            total_amount='50.00',
            is_paid=True,
        )

        response = self.client.get(reverse('receipt', args=[order.id]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Receipt.objects.filter(order=order).exists())

    def test_receipt_view_renders_existing_receipt(self):
        order = Order.objects.create(
            user=self.user,
            total_amount='50.00',
            is_paid=True,
        )
        Payment.objects.create(
            order=order,
            payment_method='CASH',
            amount_paid='50.00',
        )
        Receipt.objects.create(order=order)

        response = self.client.get(reverse('receipt', args=[order.id]))

        self.assertEqual(response.status_code, 200)

    def test_receipt_view_redirects_anonymous_user_to_login(self):
        self.client.logout()

        response = self.client.get(reverse('receipt', args=[1]))

        self.assertRedirects(response, '/login/?next=/receipt/1/')


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class PaymentConsistencyCommandTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='command_user',
            password='testpass123',
            user_code='67890',
            role='student',
        )

    def test_command_reports_detected_issues(self):
        paid_missing_all = Order.objects.create(
            user=self.user,
            total_amount='120.00',
            is_paid=True,
        )
        paid_with_mismatch = Order.objects.create(
            user=self.user,
            total_amount='80.00',
            is_paid=True,
        )
        Payment.objects.create(
            order=paid_with_mismatch,
            payment_method='CASH',
            amount_paid='60.00',
        )
        Receipt.objects.create(order=paid_with_mismatch)

        unpaid_with_payment = Order.objects.create(
            user=self.user,
            total_amount='40.00',
            is_paid=False,
        )
        Payment.objects.create(
            order=unpaid_with_payment,
            payment_method='CASH',
            amount_paid='40.00',
        )

        out = StringIO()
        call_command('payment_consistency', stdout=out)
        output = out.getvalue()

        self.assertIn('Missing payments for paid orders: 1', output)
        self.assertIn(str(paid_missing_all.id), output)
        self.assertIn('Missing receipts for paid orders: 1', output)
        self.assertIn('Payment amount mismatches: 1', output)
        self.assertIn(str(paid_with_mismatch.id), output)
        self.assertIn('Unpaid orders with payments: 1', output)
        self.assertIn(str(unpaid_with_payment.id), output)

    def test_command_repair_creates_missing_rows_and_syncs_amounts(self):
        paid_missing_all = Order.objects.create(
            user=self.user,
            total_amount='120.00',
            is_paid=True,
        )
        paid_with_mismatch = Order.objects.create(
            user=self.user,
            total_amount='80.00',
            is_paid=True,
        )
        mismatch_payment = Payment.objects.create(
            order=paid_with_mismatch,
            payment_method='CASH',
            amount_paid='60.00',
        )

        out = StringIO()
        call_command('payment_consistency', '--repair', stdout=out)
        output = out.getvalue()

        self.assertIn('Repairs applied: payments=1, receipts=2, amounts=1', output)
        self.assertTrue(Payment.objects.filter(order=paid_missing_all).exists())
        self.assertTrue(Receipt.objects.filter(order=paid_missing_all).exists())
        self.assertTrue(Receipt.objects.filter(order=paid_with_mismatch).exists())

        mismatch_payment.refresh_from_db()
        self.assertEqual(mismatch_payment.amount_paid, Decimal('80.00'))

    def test_command_fail_on_issues_raises_error(self):
        Order.objects.create(
            user=self.user,
            total_amount='120.00',
            is_paid=True,
        )

        with self.assertRaises(CommandError):
            call_command('payment_consistency', '--fail-on-issues', stdout=StringIO())
