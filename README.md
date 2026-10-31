# SubLedger

Simplified SaaS billing backend (Django + Django REST Framework): plans, customers, subscriptions, invoices, payments and an append-only ledger. Design is in [DESIGN.md](DESIGN.md).

## Setup

### Local (SQLite)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set DJANGO_SECRET_KEY
set -a; source .env; set +a
python manage.py migrate
python manage.py runserver
```

### Docker (PostgreSQL)
```bash
cp .env.example .env            # set DJANGO_SECRET_KEY and DB_PASSWORD
docker compose up --build
```

API docs (Swagger UI): http://localhost:8000/api/docs · OpenAPI: `/api/schema`

### Tests
```bash
DJANGO_SECRET_KEY=test python manage.py test
```

## API

| Method | Endpoint | Purpose |
| :-- | :-- | :-- |
| POST | /plans | Create a plan |
| GET | /plans?status= | List plans |
| PATCH | /plans/{plan_id} | Update / deactivate a plan |
| POST | /customers | Create a customer |
| GET | /customers | List customers |
| GET | /customers/{customer_id} | Fetch customer |
| POST | /subscriptions | Create a subscription (active immediately) |
| GET | /subscriptions?customer_id=&status= | List subscriptions |
| PATCH | /subscriptions/{subscription_id}/cancel | Cancel |
| POST | /invoices/generate | Generate invoice for a subscription |
| GET | /invoices/{invoice_id} | Fetch invoice |
| POST | /payments/record | Record a payment attempt |
| GET | /customers/{customer_id}/ledger | Customer ledger history |

Errors are `{"error": {"code": ..., "message": ...}}`: 400 invalid input (field errors, DRF format), 404 not found, 409 conflict (duplicates), 422 business-rule violation. Decimals are returned as strings; timestamps are ISO 8601 UTC.

### API details

#### POST /plans
Request:
```json
{"name": "Pro", "description": "Pro tier", "billing_cycle": "monthly", "price": "100.00", "currency": "USD", "status": "active"}
```
`billing_cycle`: `monthly` | `quarterly` | `yearly`. `price` > 0. `currency`: 3 uppercase letters. `description` and `status` (default `active`) are optional.

Response `201`:
```json
{"id": 1, "name": "Pro", "description": "Pro tier", "billing_cycle": "monthly", "price": "100.00", "currency": "USD", "status": "active", "created_at": "2026-10-29T12:00:00Z", "updated_at": "2026-10-29T12:00:00Z"}
```
Errors: `400` invalid or `price <= 0`.

#### GET /plans
Optional query: `status=active|inactive`. Response `200`: array of plan objects (as above).

#### PATCH /plans/{plan_id}
Request: any subset of the create fields. Deactivate with:
```json
{"status": "inactive"}
```
Response `200`: updated plan object. Errors: `400` invalid, `404` plan not found. Price/status changes apply only to future subscriptions and invoices.

#### POST /customers
Request:
```json
{"name": "Ann Lee", "email": "ann@acme.com", "company_name": "Acme", "status": "active"}
```
`company_name` and `status` (default `active`) are optional.

Response `201`:
```json
{"id": 1, "name": "Ann Lee", "email": "ann@acme.com", "company_name": "Acme", "status": "active", "created_at": "2026-10-29T12:00:00Z"}
```
Errors: `400` invalid email, `409` email already exists (case-insensitive).

#### GET /customers
Response `200`: array of customer objects.

#### GET /customers/{customer_id}
Response `200`: customer object. Errors: `404`.

#### POST /subscriptions
Request:
```json
{"customer_id": 1, "plan_id": 1, "start_date": "2026-10-29"}
```
`start_date` is optional (defaults to today).

Response `201`:
```json
{"id": 1, "customer_id": 1, "plan_id": 1, "status": "active", "start_date": "2026-10-29", "current_period_start": "2026-10-29", "current_period_end": "2026-11-29", "cancelled_at": null}
```
Errors: `404` customer or plan not found, `409` customer already has an active subscription to this plan, `422` plan or customer is inactive.

#### GET /subscriptions
Optional query: `customer_id=<int>`, `status=active|cancelled`. Response `200`: array of subscription objects. `400` on invalid filters.

#### PATCH /subscriptions/{subscription_id}/cancel
No request body. Response `200`: subscription with `"status": "cancelled"` and `cancelled_at` set. Errors: `404`, `409` already cancelled.

#### POST /invoices/generate
Request (bills the subscription's current period, then advances it):
```json
{"subscription_id": 1}
```
Or an explicit period (both fields required together; subscription period is not advanced):
```json
{"subscription_id": 1, "period_start": "2026-10-29", "period_end": "2026-11-29"}
```
Response `201`:
```json
{"id": 1, "subscription_id": 1, "customer_id": 1, "amount_due": "100.00", "amount_paid": "0.00", "currency": "USD", "status": "issued", "period_start": "2026-10-29", "period_end": "2026-11-29", "due_date": "2026-11-12", "created_at": "2026-10-29T12:00:00Z"}
```
`amount_due` is the plan price at generation time. Also appends an `invoice_created` ledger entry. Errors: `400` invalid or only one period date given, `404` subscription not found, `422` subscription not active, `period_end <= period_start`, or an invoice already exists for that period.

#### GET /invoices/{invoice_id}
Response `200`: invoice object. Errors: `404`.

#### POST /payments/record
Request (success):
```json
{"invoice_id": 1, "amount": "40.00", "currency": "USD", "status": "success", "provider_reference": "pay_123"}
```
Request (failure):
```json
{"invoice_id": 1, "amount": "100.00", "currency": "USD", "status": "failed", "provider_reference": "pay_124", "failure_reason": "card_declined"}
```
`status`: `success` | `failed`. `amount` > 0. `provider_reference` and `failure_reason` are optional.

Response `201`:
```json
{
  "payment_attempt": {"id": 1, "invoice_id": 1, "amount": "40.00", "currency": "USD", "status": "success", "provider_reference": "pay_123", "failure_reason": "", "created_at": "2026-10-29T12:05:00Z"},
  "invoice": {"id": 1, "subscription_id": 1, "customer_id": 1, "amount_due": "100.00", "amount_paid": "40.00", "currency": "USD", "status": "partially_paid", "period_start": "2026-10-29", "period_end": "2026-11-29", "due_date": "2026-11-12", "created_at": "2026-10-29T12:00:00Z"}
}
```
A successful payment raises `amount_paid` and moves the invoice to `partially_paid` or `paid`. A failed payment leaves the invoice unchanged. Either appends a `payment_success` / `payment_failure` ledger entry. Errors: `400` invalid, `404` invoice not found, `422` invoice is `paid`/`draft`/`void`, currency mismatch, or a successful amount exceeding the remaining unpaid amount.

#### GET /customers/{customer_id}/ledger
Response `200`: entries in insertion order.
```json
[
  {"id": 1, "customer_id": 1, "invoice_id": 1, "entry_type": "invoice_created", "amount": "100.00", "currency": "USD", "reference_id": "invoice:1", "description": "Invoice for 2026-10-29 to 2026-11-29", "created_at": "2026-10-29T12:00:00Z"},
  {"id": 2, "customer_id": 1, "invoice_id": 1, "entry_type": "payment_success", "amount": "40.00", "currency": "USD", "reference_id": "payment_attempt:1", "description": "", "created_at": "2026-10-29T12:05:00Z"}
]
```
`entry_type`: `invoice_created` | `payment_success` | `payment_failure`. Errors: `404` customer not found.

## Assumptions
- Amounts are `Decimal(12,2)`; currency is a 3-letter uppercase code. A payment's currency must match the invoice's.
- A subscription is active on creation; "activate" is create. `period_end` is exclusive (the start of the next period).
- `POST /invoices/generate` without a period bills the subscription's current period, then advances it. With an explicit `period_start`/`period_end` pair the subscription period is untouched. One non-void invoice per subscription period.
- Ledger amounts are positive; `entry_type` gives the direction. `reference_id` is `invoice:<id>` or `payment_attempt:<id>`.
- Customer emails are compared case-insensitively (stored lowercased).

## Limitations
- No authentication/RBAC (out of scope per the brief). Do not expose this service publicly as-is.
- `overdue` and `void` invoice statuses exist but nothing sets them yet (no scheduler / void endpoint).
- No idempotency on `provider_reference`; a retried request records a second attempt.
- No rate limiting; no pagination on list endpoints.
