from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from orders.models import Order
from payments.models import Payment, Receipt


def _collect_issues():
    paid_orders = Order.objects.filter(is_paid=True)
    payment_mismatches = Payment.objects.exclude(amount_paid=F('order__total_amount'))

    return {
        'paid_order_ids': list(paid_orders.values_list('id', flat=True)),
        'missing_payment_ids': list(
            paid_orders.filter(payment__isnull=True).values_list('id', flat=True)
        ),
        'missing_receipt_ids': list(
            paid_orders.filter(receipt__isnull=True).values_list('id', flat=True)
        ),
        'payment_mismatch_ids': list(payment_mismatches.values_list('order_id', flat=True)),
        'unpaid_with_payment_ids': list(
            Order.objects.filter(is_paid=False, payment__isnull=False).values_list('id', flat=True)
        ),
        'unpaid_with_receipt_ids': list(
            Order.objects.filter(is_paid=False, receipt__isnull=False).values_list('id', flat=True)
        ),
    }


def _format_ids(order_ids):
    if not order_ids:
        return 'none'
    return ', '.join(str(order_id) for order_id in order_ids)


class Command(BaseCommand):
    help = 'Audit and optionally repair payment and receipt consistency for orders.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--repair',
            action='store_true',
            help='Create missing payments/receipts for paid orders and sync mismatched amounts.',
        )
        parser.add_argument(
            '--fail-on-issues',
            action='store_true',
            help='Exit with an error code when any consistency issues are found.',
        )

    def handle(self, *args, **options):
        repair = options['repair']
        fail_on_issues = options['fail_on_issues']

        issues = _collect_issues()
        self._write_report('Current payment consistency audit', issues)

        repaired_payments = 0
        repaired_receipts = 0
        repaired_amounts = 0

        if repair:
            with transaction.atomic():
                for order in Order.objects.filter(id__in=issues['missing_payment_ids']):
                    Payment.objects.create(
                        order=order,
                        payment_method='CASH',
                        amount_paid=order.total_amount,
                    )
                    repaired_payments += 1

                for order in Order.objects.filter(id__in=issues['missing_receipt_ids']):
                    Receipt.objects.create(order=order)
                    repaired_receipts += 1

                mismatched_payments = Payment.objects.select_related('order').filter(
                    order_id__in=issues['payment_mismatch_ids']
                )
                for payment in mismatched_payments:
                    payment.amount_paid = payment.order.total_amount
                    payment.save(update_fields=['amount_paid'])
                    repaired_amounts += 1

            self.stdout.write(
                self.style.SUCCESS(
                    'Repairs applied: '
                    f'payments={repaired_payments}, '
                    f'receipts={repaired_receipts}, '
                    f'amounts={repaired_amounts}'
                )
            )
            issues = _collect_issues()
            self._write_report('Post-repair audit', issues)

        remaining_issue_count = (
            len(issues['missing_payment_ids'])
            + len(issues['missing_receipt_ids'])
            + len(issues['payment_mismatch_ids'])
            + len(issues['unpaid_with_payment_ids'])
            + len(issues['unpaid_with_receipt_ids'])
        )

        if remaining_issue_count == 0:
            self.stdout.write(self.style.SUCCESS('No payment consistency issues found.'))
            return

        if fail_on_issues:
            raise CommandError('Payment consistency issues found.')

    def _write_report(self, title, issues):
        self.stdout.write(title)
        self.stdout.write(f"Paid orders: {len(issues['paid_order_ids'])}")
        self.stdout.write(
            'Missing payments for paid orders: '
            f"{len(issues['missing_payment_ids'])} "
            f"({_format_ids(issues['missing_payment_ids'])})"
        )
        self.stdout.write(
            'Missing receipts for paid orders: '
            f"{len(issues['missing_receipt_ids'])} "
            f"({_format_ids(issues['missing_receipt_ids'])})"
        )
        self.stdout.write(
            'Payment amount mismatches: '
            f"{len(issues['payment_mismatch_ids'])} "
            f"({_format_ids(issues['payment_mismatch_ids'])})"
        )
        self.stdout.write(
            'Unpaid orders with payments: '
            f"{len(issues['unpaid_with_payment_ids'])} "
            f"({_format_ids(issues['unpaid_with_payment_ids'])})"
        )
        self.stdout.write(
            'Unpaid orders with receipts: '
            f"{len(issues['unpaid_with_receipt_ids'])} "
            f"({_format_ids(issues['unpaid_with_receipt_ids'])})"
        )
