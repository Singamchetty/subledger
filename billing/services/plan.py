from decimal import Decimal

from ..exceptions import BusinessRuleError, NotFoundError


class PlanService:
    def __init__(self, plan_repo):
        self.plan_repo = plan_repo

    def create_plan(self, data: dict):
        self._validate_price(data["price"])
        return self.plan_repo.create(**data)

    def list_plans(self, status: str | None = None):
        return self.plan_repo.list(status)

    def update_plan(self, plan_id: int, changes: dict):
        plan = self.plan_repo.get(plan_id)
        if plan is None:
            raise NotFoundError("Plan not found.")
        if "price" in changes:
            self._validate_price(changes["price"])
        # Price/status changes only affect future subscriptions and invoices.
        for field, value in changes.items():
            setattr(plan, field, value)
        return self.plan_repo.save(plan)

    @staticmethod
    def _validate_price(price: Decimal):
        if price <= 0:
            raise BusinessRuleError("Plan price must be greater than 0.")
