from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ..exceptions import BusinessRuleError, NotFoundError
from ..models import InvoiceStatus, LedgerEntryType, SubscriptionStatus
from ..periods import add_cycle


class InvoiceService:
    def __init__(self, subscription_repo, invoice_repo, ledger_service):
        self.subscription_repo = subscription_repo
        self.invoice_repo = invoice_repo
        self.ledger_service = ledger_service

    @transaction.atomic
    def generate_invoice(self, subscription_id: int, period_start=None, period_end=None):
        subscription = self.subscription_repo.get(subscription_id)
        if subscription is None:
            raise NotFoundError("Subscription not found.")
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise BusinessRuleError("Invoices can only be generated for active subscriptions.")

        uses_current_period = period_start is None
        if uses_current_period:
            period_start = subscription.current_period_start
            period_end = subscription.current_period_end
        elif period_end <= period_start:
            raise BusinessRuleError("period_end must be after period_start.")

        if self.invoice_repo.exists_for_period(subscription.id, period_start, period_end):
            raise BusinessRuleError("An invoice already exists for this billing period.")

        plan = subscription.plan
        invoice = self.invoice_repo.create(
            subscription=subscription,
            customer_id=subscription.customer_id,
            amount_due=plan.price,  # snapshot of the price at generation time
            amount_paid=0,
            currency=plan.currency,
            status=InvoiceStatus.ISSUED,
            period_start=period_start,
            period_end=period_end,
            due_date=timezone.now().date() + timedelta(days=settings.INVOICE_DUE_DAYS),
        )
        self.ledger_service.record(
            invoice=invoice,
            entry_type=LedgerEntryType.INVOICE_CREATED,
            amount=invoice.amount_due,
            reference_id=f"invoice:{invoice.id}",
            description=f"Invoice for {period_start} to {period_end}",
        )

        if uses_current_period:
            subscription.current_period_start = period_end
            subscription.current_period_end = add_cycle(period_end, plan.billing_cycle)
            self.subscription_repo.save(subscription)
        return invoice

    def get_invoice(self, invoice_id: int):
        invoice = self.invoice_repo.get(invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice not found.")
        return invoice

    def apply_successful_payment(self, invoice, amount):
        """Increase amount_paid and move status. Caller holds the row lock."""
        invoice.amount_paid += amount
        invoice.status = (
            InvoiceStatus.PAID
            if invoice.amount_paid >= invoice.amount_due
            else InvoiceStatus.PARTIALLY_PAID
        )
        return self.invoice_repo.save(invoice)
