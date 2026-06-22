# KMM Chaturmas ERP Architecture

## 1. Purpose

This document defines the production architecture for a Django 5 ERP that supports Chaturmas event operations for Kalyan Mitra Mandal. The system is designed as an event-scoped ERP with transaction-ledger inventory, automatic calculations, role-based access control, and auditability across every high-value workflow.

The architecture is intentionally GitHub-first. GitHub is the source of truth for code, workflows, and deployment artifacts. PythonAnywhere is treated as a deployment target, not the primary project container.

## 2. Core Architectural Principles

1. Every operational record belongs to exactly one `Event`.
2. Inventory is never manually edited. All stock changes are derived from immutable transactions.
3. Business logic lives in services, not in templates or views.
4. All calculations are derived from authoritative source records.
5. Important actions create audit logs.
6. Read models may be denormalized only when they can be recomputed from source data.
7. Multi-year support is mandatory, so the schema must not hardcode a single event year.
8. The UI must be mobile-first and usable on low-bandwidth connections.

## 3. Technology Stack

- Django 5+
- Python 3.12
- Bootstrap 5
- SQLite for development
- MySQL or MariaDB for production
- Optional HTMX for light dynamic interactions
- Local media storage initially, with future object storage compatibility

## 4. Repository Strategy

Repository structure:

```text
kmm-chaturmas-erp/
  manage.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  deployment/
    pythonanywhere.md
  media/
  static/
  config/
    settings.py
    settings_dev.py
    settings_prod.py
    urls.py
  apps/
    accounts/
    masters/
    requirements/
    sponsorship/
    vendors/
    procurement/
    inventory/
    distribution/
    funds/
    reports/
    dashboard/
    auditlog/
```

Branch strategy:

- `main` for production releases
- `develop` for integration
- feature branches for isolated work

## 5. Application Boundaries

### accounts

Handles authentication, role assignment, user profile extensions, and permissions.

### masters

Contains event-scoped master data such as items, upashrays, volunteers, sponsors, and other reference data.

### requirements

Collects item requirements by upashray and special requirements added from the field.

### sponsorship

Tracks sponsor commitments, receipts, and sponsorship coverage by item and event.

### vendors

Stores vendor details, quotation history, and preferred vendor scoring.

### procurement

Handles purchase planning, purchase orders, and goods receipt workflows.

### inventory

Owns the stock ledger, derived balances, reservations, and inventory projections.

### distribution

Manages distribution batches, dispatch, delivery, and reconciliation.

### funds

Stores donations, expenses, transfers, and fund balance projections.

### reports

Provides printable, exportable, and downloadable operational reports.

### dashboard

Contains the home screen, Item Control Center, KPI cards, and operational summaries.

### auditlog

Stores activity logs and compliance-grade event trails.

## 6. Data Architecture

The system uses a normalized transactional core with derived projections.

### Authoritative sources

- Requirement headers and lines
- Sponsorship commitments and receipts
- Purchase orders and goods receipts
- Inventory transactions
- Distribution records
- Fund transactions
- Audit logs

### Derived projections

- Item demand summary
- Sponsorship coverage summary
- Stock balance summary
- Purchase need summary
- Distribution progress summary
- Fund summary

Derived values should be calculated through services or database annotations, then cached only when necessary for performance.

## 7. Event Scoping

Every business object that affects operations must include `event`.

This includes:

- Items
- Upashrays
- Volunteers
- Sponsors
- Vendors when event-specific vendor data is required
- Requirements
- Sponsorship commitments
- Procurement records
- Inventory transactions
- Distribution records
- Fund records
- Audit logs

This is the key architectural decision that allows multi-year and multi-event support without schema redesign.

## 8. Inventory Architecture

Inventory must be ledger-based.

### Rules

- No stock field may be edited directly by users.
- Every receipt, distribution, return, damage entry, or adjustment creates a transaction row.
- Current stock is derived from transaction sums.
- Reversals should create compensating entries instead of overwriting prior records.

### Transaction types

- Purchase receipt
- Donation receipt
- Sponsorship receipt
- Distribution dispatch
- Return
- Damage
- Adjustment

### Inventory projections

For operational speed, the system may maintain computed summary tables or annotated querysets for:

- Current stock
- Reserved stock
- Available stock
- Distributed quantity
- Pending purchase need

These projections must remain derivable from transaction history.

## 9. Business Logic Pattern

### Views

Use class-based views for CRUD, filtering, and workflow transitions.

### Services

All state changes should pass through service functions that:

- Validate business rules
- Create transactional records
- Update derived summaries
- Create audit logs
- Enforce event scope

### Query helpers

Use repository-style read helpers where complex dashboard and reporting queries are repeated across screens.

### Templates

Templates must remain presentation-only. They should not implement business rules or calculations beyond display formatting.

## 10. Authentication and Authorization

Recommended role model:

- Super Admin
- Procurement Team
- Sponsorship Team
- Distribution Team
- Accounts Team
- Viewer

Permissions should be enforced at the view and service layers, not only in the UI.

Suggested access model:

- Django groups for coarse roles
- Fine-grained model permissions for CRUD
- Workflow permissions for state transitions

## 11. UI Architecture

Frontend requirements:

- Bootstrap 5
- Mobile-first responsive layout
- Compact admin-style operational screens
- Reusable partials for tables, filters, badges, summary cards, and alerts
- Pagination for all large datasets
- Search and filter controls everywhere that operators need to scan data quickly

The Item Control Center is the first post-login screen and the operational command center.

## 12. Integration and Import Strategy

Importers should be staged:

1. Upload spreadsheet
2. Validate rows
3. Preview errors
4. Commit into domain tables

Target import sets:

- Items
- Upashrays
- Volunteers
- Sponsors
- Vendor rates

Exports should be available in:

- Excel
- PDF
- Print-friendly HTML

## 13. Audit and Compliance

Every important change should generate an audit row capturing:

- User
- Action
- Module
- Record ID
- Old value
- New value
- Timestamp

Audit trails should be append-only. Business records may be soft-deleted when needed, but the audit trail must retain the history.

## 14. Performance and Scale

The design must support:

- 1000+ sponsors
- 500+ volunteers
- 500+ upashrays
- 10000+ inventory transactions
- 100 concurrent users

Scalability tactics:

- Index foreign keys and lookup fields
- Use pagination on every large list
- Prefer annotated summaries over repeated Python loops
- Cache only derived dashboards, not source data
- Use MySQL/MariaDB in production for concurrency-heavy workloads

## 15. Deployment Architecture

### Development

- SQLite
- Local media files
- `.env` driven settings

### Production

- MySQL or MariaDB
- Static file collection
- Secure environment variables
- GitHub-managed source code

### PythonAnywhere

Deployment should consist of:

- Pull latest code
- Install dependencies
- Run migrations
- Collect static files
- Reload the web app

## 16. Suggested Improvements Beyond the Spec

- Add `Event` as a first-class model from the beginning.
- Add reversible transactions for audit-safe corrections.
- Add staged imports instead of direct CSV writes.
- Add attachment support for receipts, quotations, and delivery evidence.
- Add a dashboard cache invalidation strategy for expensive summaries.
- Add status history tables for key workflows where traceability matters.

