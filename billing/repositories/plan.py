from ..models import Plan


class PlanRepository:
    def create(self, **fields) -> Plan:
        return Plan.objects.create(**fields)

    def get(self, plan_id: int) -> Plan | None:
        return Plan.objects.filter(pk=plan_id).first()

    def list(self, status: str | None = None):
        qs = Plan.objects.order_by("id")
        return qs.filter(status=status) if status else qs

    def save(self, plan: Plan) -> Plan:
        plan.save()
        return plan
