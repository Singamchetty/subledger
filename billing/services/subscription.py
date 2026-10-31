from django.utils import timezone

from ..exceptions import BusinessRuleError, ConflictError, NotFoundError
from ..models import CustomerStatus, PlanStatus, SubscriptionStatus
from ..periods import add_cycle


class SubscriptionService:
    def __init__(self, subscription_repo, plan_repo, customer_repo):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.customer_repo = customer_repo

    def create_subscription(self, customer_id: int, plan_id: int, start_date=None):
        customer = self.customer_repo.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found.")
        if customer.status != CustomerStatus.ACTIVE:
            raise BusinessRuleError("Customer is not active.")

        plan = self.plan_repo.get(plan_id)
        if plan is None:
            raise NotFoundError("Plan not found.")
        if plan.status != PlanStatus.ACTIVE:
            raise BusinessRuleError("Cannot subscribe to an inactive plan.")

        if self.subscription_repo.get_active(customer_id, plan_id):
            raise ConflictError(
                "Customer already has an active subscription to this plan."
            )

        start = start_date or timezone.now().date()
        return self.subscription_repo.create(
            customer=customer,
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=start,
            current_period_start=start,
            current_period_end=add_cycle(start, plan.billing_cycle),
        )

    def get_subscription(self, subscription_id: int):
        subscription = self.subscription_repo.get(subscription_id)
        if subscription is None:
            raise NotFoundError("Subscription not found.")
        return subscription

    def list_subscriptions(self, customer_id=None, status=None):
        return self.subscription_repo.list(customer_id, status)

    def cancel_subscription(self, subscription_id: int):
        subscription = self.get_subscription(subscription_id)
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise ConflictError("Subscription is already cancelled.")
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = timezone.now()
        return self.subscription_repo.save(subscription)
