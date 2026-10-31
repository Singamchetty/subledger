from django.db import transaction

from ..exceptions import BusinessRuleError, NotFoundError
from ..models import InvoiceStatus, LedgerEntryType, PaymentStatus

PAYABLE_STATUSES = {
    InvoiceStatus.ISSUED,
    InvoiceStatus.PARTIALLY_PAID,
    InvoiceStatus.OVERDUE,
}


class PaymentService:
    def __init__(self, invoice_repo, payment_attempt_repo, invoice_service, ledger_service):
        self.invoice_repo = invoice_repo
        self.payment_attempt_repo = payment_attempt_repo
        self.invoice_service = invoice_service
        self.ledger_service = ledger_service

    @transaction.atomic
    def record_payment(
        self,
        invoice_id: int,
        amount,
        currency: str,
        status: str,
        provider_reference: str = "",
        failure_reason: str = "",
    ):
        invoice = self.invoice_repo.get_for_update(invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice not found.")
        if invoice.status not in PAYABLE_STATUSES:
            raise BusinessRuleError(f"Invoice is {invoice.status} and cannot accept payments.")
        if currency != invoice.currency:
            raise BusinessRuleError("Payment currency does not match invoice currency.")
        if amount <= 0:
            raise BusinessRuleError("Payment amount must be greater than 0.")

        succeeded = status == PaymentStatus.SUCCESS
        remaining = invoice.amount_due - invoice.amount_paid
        if succeeded and amount > remaining:
            raise BusinessRuleError("Payment exceeds the remaining unpaid amount.")

        attempt = self.payment_attempt_repo.create(
            invoice=invoice,
            amount=amount,
            currency=currency,
            status=status,
            provider_reference=provider_reference,
            failure_reason="" if succeeded else failure_reason,
        )

        if succeeded:
            invoice = self.invoice_service.apply_successful_payment(invoice, amount)
        # A failed attempt leaves amount_paid and invoice status untouched.

        self.ledger_service.record(
            invoice=invoice,
            entry_type=(
                LedgerEntryType.PAYMENT_SUCCESS if succeeded else LedgerEntryType.PAYMENT_FAILURE
            ),
            amount=amount,
            reference_id=f"payment_attempt:{attempt.id}",
            description="" if succeeded else failure_reason,
        )
        return attempt, invoice
