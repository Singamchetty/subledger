from decimal import Decimal

from rest_framework import serializers

from .models import (
    BillingCycle,
    Customer,
    CustomerStatus,
    Invoice,
    LedgerEntry,
    PaymentAttempt,
    PaymentStatus,
    Plan,
    PlanStatus,
    Subscription,
    SubscriptionStatus,
)

# ---- Input schemas -------------------------------------------------------


class InputSchema(serializers.Serializer):
    @classmethod
    def validated(cls, data):
        """Validate against this schema and return only the declared fields."""
        schema = cls(data=data)
        schema.is_valid(raise_exception=True)
        return schema.validated_data


class PlanCreateSchema(InputSchema):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    billing_cycle = serializers.ChoiceField(choices=BillingCycle.choices)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3)
    status = serializers.ChoiceField(choices=PlanStatus.choices, default=PlanStatus.ACTIVE)


class PlanUpdateSchema(InputSchema):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    billing_cycle = serializers.ChoiceField(choices=BillingCycle.choices, required=False)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"), required=False
    )
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3, required=False)
    status = serializers.ChoiceField(choices=PlanStatus.choices, required=False)


class CustomerCreateSchema(InputSchema):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    company_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(choices=CustomerStatus.choices, default=CustomerStatus.ACTIVE)


class SubscriptionCreateSchema(InputSchema):
    customer_id = serializers.IntegerField(min_value=1)
    plan_id = serializers.IntegerField(min_value=1)
    start_date = serializers.DateField(required=False)


class SubscriptionFilterSchema(InputSchema):
    customer_id = serializers.IntegerField(min_value=1, required=False)
    status = serializers.ChoiceField(choices=SubscriptionStatus.choices, required=False)


class InvoiceGenerateSchema(InputSchema):
    subscription_id = serializers.IntegerField(min_value=1)
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)

    def validate(self, attrs):
        if ("period_start" in attrs) != ("period_end" in attrs):
            raise serializers.ValidationError(
                "period_start and period_end must be provided together."
            )
        return attrs


class PaymentRecordSchema(InputSchema):
    invoice_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    currency = serializers.RegexField(r"^[A-Z]{3}$", max_length=3)
    status = serializers.ChoiceField(choices=PaymentStatus.choices)
    provider_reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    failure_reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


# ---- Output schemas ------------------------------------------------------


class PlanSchema(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id", "name", "description", "billing_cycle", "price",
            "currency", "status", "created_at", "updated_at",
        ]


class CustomerSchema(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "company_name", "status", "created_at"]


class SubscriptionSchema(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id", "customer_id", "plan_id", "status", "start_date",
            "current_period_start", "current_period_end", "cancelled_at",
        ]


class InvoiceSchema(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id", "subscription_id", "customer_id", "amount_due", "amount_paid",
            "currency", "status", "period_start", "period_end", "due_date", "created_at",
        ]


class PaymentAttemptSchema(serializers.ModelSerializer):
    class Meta:
        model = PaymentAttempt
        fields = [
            "id", "invoice_id", "amount", "currency", "status",
            "provider_reference", "failure_reason", "created_at",
        ]


class PaymentResultSchema(serializers.Serializer):
    payment_attempt = PaymentAttemptSchema()
    invoice = InvoiceSchema()


class LedgerEntrySchema(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id", "customer_id", "invoice_id", "entry_type", "amount",
            "currency", "reference_id", "description", "created_at",
        ]
