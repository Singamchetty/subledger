"""Composition root: the only place that wires repositories into services."""
from .repositories import (
    CustomerRepository,
    InvoiceRepository,
    LedgerRepository,
    PaymentAttemptRepository,
    PlanRepository,
    SubscriptionRepository,
)
from .services import (
    CustomerService,
    InvoiceService,
    LedgerService,
    PaymentService,
    PlanService,
    SubscriptionService,
)


def get_plan_service() -> PlanService:
    return PlanService(PlanRepository())


def get_customer_service() -> CustomerService:
    return CustomerService(CustomerRepository())


def get_subscription_service() -> SubscriptionService:
    return SubscriptionService(
        SubscriptionRepository(), PlanRepository(), CustomerRepository()
    )


def get_ledger_service() -> LedgerService:
    return LedgerService(LedgerRepository(), CustomerRepository())


def get_invoice_service() -> InvoiceService:
    return InvoiceService(
        SubscriptionRepository(), InvoiceRepository(), get_ledger_service()
    )


def get_payment_service() -> PaymentService:
    return PaymentService(
        InvoiceRepository(),
        PaymentAttemptRepository(),
        get_invoice_service(),
        get_ledger_service(),
    )
