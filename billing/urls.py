from django.urls import path

from .views import customers, invoices, payments, plans, subscriptions

urlpatterns = [
    path("plans", plans.PlanListCreateView.as_view()),
    path("plans/<int:plan_id>", plans.PlanDetailView.as_view()),
    path("customers", customers.CustomerListCreateView.as_view()),
    path("customers/<int:customer_id>", customers.CustomerDetailView.as_view()),
    path("customers/<int:customer_id>/ledger", customers.CustomerLedgerView.as_view()),
    path("subscriptions", subscriptions.SubscriptionListCreateView.as_view()),
    path(
        "subscriptions/<int:subscription_id>/cancel",
        subscriptions.SubscriptionCancelView.as_view(),
    ),
    path("invoices/generate", invoices.InvoiceGenerateView.as_view()),
    path("invoices/<int:invoice_id>", invoices.InvoiceDetailView.as_view()),
    path("payments/record", payments.PaymentRecordView.as_view()),
]
