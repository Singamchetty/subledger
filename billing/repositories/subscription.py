from django.db import IntegrityError, transaction

from ..exceptions import ConflictError
from ..models import Subscription, SubscriptionStatus


class SubscriptionRepository:
    def create(self, **fields) -> Subscription:
        try:
            with transaction.atomic():
                return Subscription.objects.create(**fields)
        except IntegrityError:
            raise ConflictError(
                "Customer already has an active subscription to this plan."
            )

    def get(self, subscription_id: int) -> Subscription | None:
        return (
            Subscription.objects.select_related("plan")
            .filter(pk=subscription_id)
            .first()
        )

    def get_active(self, customer_id: int, plan_id: int) -> Subscription | None:
        return Subscription.objects.filter(
            customer_id=customer_id, plan_id=plan_id, status=SubscriptionStatus.ACTIVE
        ).first()

    def list(self, customer_id: int | None = None, status: str | None = None):
        qs = Subscription.objects.order_by("id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    def save(self, subscription: Subscription) -> Subscription:
        subscription.save()
        return subscription
