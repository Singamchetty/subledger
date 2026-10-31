from ..models import LedgerEntry


class LedgerRepository:
    """Insert and read only. There is deliberately no update or delete."""

    def append(self, **fields) -> LedgerEntry:
        return LedgerEntry.objects.create(**fields)

    def list_for_customer(self, customer_id: int):
        return LedgerEntry.objects.filter(customer_id=customer_id).order_by("id")
