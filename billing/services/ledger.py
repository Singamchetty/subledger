from ..exceptions import NotFoundError


class LedgerService:
    """Only ever appends. Amounts are positive; entry_type gives the direction."""

    def __init__(self, ledger_repo, customer_repo):
        self.ledger_repo = ledger_repo
        self.customer_repo = customer_repo

    def record(self, *, invoice, entry_type, amount, reference_id, description=""):
        return self.ledger_repo.append(
            customer_id=invoice.customer_id,
            invoice=invoice,
            entry_type=entry_type,
            amount=amount,
            currency=invoice.currency,
            reference_id=reference_id,
            description=description,
        )

    def get_customer_ledger(self, customer_id: int):
        if self.customer_repo.get(customer_id) is None:
            raise NotFoundError("Customer not found.")
        return self.ledger_repo.list_for_customer(customer_id)
