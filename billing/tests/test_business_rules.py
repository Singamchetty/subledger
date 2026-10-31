from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from billing.models import LedgerEntry


class BillingTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def make_plan(self, **overrides):
        body = {
            "name": "Pro", "billing_cycle": "monthly", "price": "100.00", "currency": "USD",
            **overrides,
        }
        return self.client.post("/plans", body, format="json")

    def make_customer(self, email="a@example.com"):
        return self.client.post(
            "/customers", {"name": "Ann", "email": email, "company_name": "Acme"}, format="json"
        )

    def make_subscription(self):
        plan = self.make_plan().json()
        customer = self.make_customer().json()
        sub = self.client.post(
            "/subscriptions", {"customer_id": customer["id"], "plan_id": plan["id"]}, format="json"
        ).json()
        return plan, customer, sub

    def make_invoice(self):
        plan, customer, sub = self.make_subscription()
        invoice = self.client.post(
            "/invoices/generate", {"subscription_id": sub["id"]}, format="json"
        ).json()
        return plan, customer, sub, invoice

    def pay(self, invoice_id, amount, status="success", **extra):
        return self.client.post(
            "/payments/record",
            {"invoice_id": invoice_id, "amount": amount, "currency": "USD",
             "status": status, "provider_reference": "pay_1", **extra},
            format="json",
        )


class PlanAndCustomerRules(BillingTestCase):
    def test_plan_price_must_be_positive(self):
        self.assertEqual(self.make_plan(price="0").status_code, 400)
        self.assertEqual(self.make_plan(price="-5").status_code, 400)

    def test_plan_can_be_deactivated(self):
        plan = self.make_plan().json()
        res = self.client.patch(f"/plans/{plan['id']}", {"status": "inactive"}, format="json")
        self.assertEqual(res.json()["status"], "inactive")

    def test_customer_email_must_be_unique(self):
        self.assertEqual(self.make_customer("dup@example.com").status_code, 201)
        res = self.make_customer("DUP@example.com")
        self.assertEqual(res.status_code, 409)


class SubscriptionRules(BillingTestCase):
    def test_cannot_subscribe_to_inactive_plan(self):
        plan = self.make_plan(status="inactive").json()
        customer = self.make_customer().json()
        res = self.client.post(
            "/subscriptions", {"customer_id": customer["id"], "plan_id": plan["id"]}, format="json"
        )
        self.assertEqual(res.status_code, 422)

    def test_no_duplicate_active_subscription_to_same_plan(self):
        plan, customer, _ = self.make_subscription()
        res = self.client.post(
            "/subscriptions", {"customer_id": customer["id"], "plan_id": plan["id"]}, format="json"
        )
        self.assertEqual(res.status_code, 409)

    def test_can_resubscribe_after_cancel(self):
        plan, customer, sub = self.make_subscription()
        self.assertEqual(self.client.patch(f"/subscriptions/{sub['id']}/cancel").json()["status"], "cancelled")
        res = self.client.post(
            "/subscriptions", {"customer_id": customer["id"], "plan_id": plan["id"]}, format="json"
        )
        self.assertEqual(res.status_code, 201)


class InvoiceAndPaymentRules(BillingTestCase):
    def test_invoice_amount_uses_plan_price_at_generation_time(self):
        plan, _, sub = self.make_subscription()
        self.client.patch(f"/plans/{plan['id']}", {"price": "250.00"}, format="json")
        invoice = self.client.post(
            "/invoices/generate", {"subscription_id": sub["id"]}, format="json"
        ).json()
        self.assertEqual(Decimal(invoice["amount_due"]), Decimal("250.00"))
        self.assertEqual(invoice["status"], "issued")

    def test_invoice_requires_active_subscription(self):
        _, _, sub = self.make_subscription()
        self.client.patch(f"/subscriptions/{sub['id']}/cancel")
        res = self.client.post("/invoices/generate", {"subscription_id": sub["id"]}, format="json")
        self.assertEqual(res.status_code, 422)

    def test_partial_then_full_payment_updates_status(self):
        *_, invoice = self.make_invoice()
        res = self.pay(invoice["id"], "40.00").json()
        self.assertEqual(res["invoice"]["status"], "partially_paid")
        self.assertEqual(Decimal(res["invoice"]["amount_paid"]), Decimal("40.00"))
        res = self.pay(invoice["id"], "60.00").json()
        self.assertEqual(res["invoice"]["status"], "paid")

    def test_payment_cannot_exceed_remaining_amount(self):
        *_, invoice = self.make_invoice()
        self.assertEqual(self.pay(invoice["id"], "100.01").status_code, 422)
        self.pay(invoice["id"], "70.00")
        self.assertEqual(self.pay(invoice["id"], "30.01").status_code, 422)

    def test_failed_payment_does_not_increase_amount_paid(self):
        *_, invoice = self.make_invoice()
        res = self.pay(invoice["id"], "100.00", status="failed", failure_reason="card_declined").json()
        self.assertEqual(res["payment_attempt"]["status"], "failed")
        self.assertEqual(Decimal(res["invoice"]["amount_paid"]), Decimal("0"))
        self.assertEqual(res["invoice"]["status"], "issued")


class LedgerRules(BillingTestCase):
    def test_ledger_records_events_traceable_by_reference_id(self):
        _, customer, _, invoice = self.make_invoice()
        failed = self.pay(invoice["id"], "100.00", status="failed", failure_reason="x").json()
        paid = self.pay(invoice["id"], "100.00").json()
        entries = self.client.get(f"/customers/{customer['id']}/ledger").json()
        self.assertEqual(
            [(e["entry_type"], e["reference_id"]) for e in entries],
            [
                ("invoice_created", f"invoice:{invoice['id']}"),
                ("payment_failure", f"payment_attempt:{failed['payment_attempt']['id']}"),
                ("payment_success", f"payment_attempt:{paid['payment_attempt']['id']}"),
            ],
        )

    def test_ledger_entries_are_append_only(self):
        self.make_invoice()
        entry = LedgerEntry.objects.first()
        entry.amount = Decimal("1.00")
        with self.assertRaises(TypeError):
            entry.save()
        with self.assertRaises(TypeError):
            entry.delete()
        with self.assertRaises(TypeError):
            LedgerEntry.objects.all().update(amount=1)
        with self.assertRaises(TypeError):
            LedgerEntry.objects.all().delete()
