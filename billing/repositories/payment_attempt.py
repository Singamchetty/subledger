from ..models import PaymentAttempt


class PaymentAttemptRepository:
    def create(self, **fields) -> PaymentAttempt:
        return PaymentAttempt.objects.create(**fields)
