from django.db import IntegrityError, transaction

from ..exceptions import ConflictError
from ..models import Customer


class CustomerRepository:
    def create(self, **fields) -> Customer:
        try:
            with transaction.atomic():
                return Customer.objects.create(**fields)
        except IntegrityError:
            # unique(email) is the source of truth; this closes the check-then-insert race.
            raise ConflictError("A customer with this email already exists.")

    def get(self, customer_id: int) -> Customer | None:
        return Customer.objects.filter(pk=customer_id).first()

    def email_exists(self, email: str) -> bool:
        return Customer.objects.filter(email__iexact=email).exists()

    def list(self):
        return Customer.objects.order_by("id")
