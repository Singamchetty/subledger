from datetime import date

from django.db import IntegrityError, transaction

from ..exceptions import ConflictError
from ..models import Invoice, InvoiceStatus


class InvoiceRepository:
    def create(self, **fields) -> Invoice:
        try:
            with transaction.atomic():
                return Invoice.objects.create(**fields)
        except IntegrityError:
            raise ConflictError("An invoice already exists for this billing period.")

    def get(self, invoice_id: int) -> Invoice | None:
        return Invoice.objects.filter(pk=invoice_id).first()

    def get_for_update(self, invoice_id: int) -> Invoice | None:
        """Row-locked fetch; call inside a transaction to serialize concurrent payments."""
        return Invoice.objects.select_for_update().filter(pk=invoice_id).first()

    def exists_for_period(
        self, subscription_id: int, period_start: date, period_end: date
    ) -> bool:
        return (
            Invoice.objects.filter(
                subscription_id=subscription_id,
                period_start=period_start,
                period_end=period_end,
            )
            .exclude(status=InvoiceStatus.VOID)
            .exists()
        )

    def save(self, invoice: Invoice) -> Invoice:
        invoice.save()
        return invoice
