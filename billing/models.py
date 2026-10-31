from django.db import models
from django.db.models import F, Q


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PlanStatus(models.TextChoices):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CustomerStatus(models.TextChoices):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class PaymentStatus(models.TextChoices):
    SUCCESS = "success"
    FAILED = "failed"


class LedgerEntryType(models.TextChoices):
    INVOICE_CREATED = "invoice_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"


class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20, choices=PlanStatus.choices, default=PlanStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plans"
        constraints = [
            models.CheckConstraint(condition=Q(price__gt=0), name="plan_price_gt_0"),
        ]


class Customer(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=20, choices=CustomerStatus.choices, default=CustomerStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customers"


class Subscription(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="subscriptions"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    start_date = models.DateField()
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscriptions"
        constraints = [
            # Base rule: one active subscription per customer per plan.
            models.UniqueConstraint(
                fields=["customer", "plan"],
                condition=Q(status="active"),
                name="one_active_subscription_per_customer_plan",
            ),
        ]


class Invoice(models.Model):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.PROTECT, related_name="invoices"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.ISSUED
    )
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices"
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_paid__gte=0) & Q(amount_paid__lte=F("amount_due")),
                name="invoice_amount_paid_within_due",
            ),
            models.UniqueConstraint(
                fields=["subscription", "period_start", "period_end"],
                condition=~Q(status="void"),
                name="one_invoice_per_subscription_period",
            ),
        ]


class PaymentAttempt(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="payment_attempts"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    provider_reference = models.CharField(max_length=100, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_attempts"
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_gt_0"),
        ]


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError("Ledger entries are append-only.")

    def delete(self):
        raise TypeError("Ledger entries are append-only.")

    def bulk_update(self, *args, **kwargs):
        raise TypeError("Ledger entries are append-only.")


class LedgerEntry(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="ledger_entries"
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="ledger_entries"
    )
    entry_type = models.CharField(max_length=30, choices=LedgerEntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    # Source record, e.g. "invoice:12" or "payment_attempt:7".
    reference_id = models.CharField(max_length=50, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = "ledger_entries"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise TypeError("Ledger entries are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("Ledger entries are append-only.")
