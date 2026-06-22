# KMM Chaturmas ERP Implementation Plan

## Phase 1 - Architecture and Planning

Deliverables:

- `architecture.md`
- `database_schema.md`
- `module_flow.md`
- `implementation_plan.md`

Objectives:

- Finalize the domain model
- Lock the event-scoping strategy
- Confirm transaction-ledger inventory design
- Define module boundaries and workflows
- Document the first-screen Item Control Center

Exit criteria:

- The team can begin project scaffolding without making major product decisions later.

## Phase 2 - Django Project Skeleton

Build the repository and Django foundation:

- Create `manage.py`, `config/`, `apps/`, `static/`, `media/`, and deployment docs
- Add environment-based settings
- Add authentication and role scaffolding
- Add base templates and Bootstrap 5 layout
- Implement the Item Control Center as the first operational screen

Domain app order:

1. `accounts`
2. `masters`
3. `requirements`
4. `sponsorship`
5. `vendors`
6. `procurement`
7. `inventory`
8. `distribution`
9. `funds`
10. `reports`
11. `dashboard`
12. `auditlog`

Phase 2 acceptance criteria:

- Each app has models, admin, forms, URLs, views, templates, services, and permissions
- No direct stock editing exists anywhere
- Dashboard values are derived from transaction and commitment data
- The app runs locally on SQLite

## Phase 3 - Reporting and Operations

Add:

- Analytics
- Import/export
- Seed data
- Backup tooling
- Deployment files
- README and admin setup docs

Phase 3 acceptance criteria:

- Reports can be exported
- Importers can stage and validate data
- Admin backup flow is available
- PythonAnywhere deployment instructions are complete

## Phase 4 - Production Hardening

Add:

- Test coverage for service rules and permissions
- Optimized queries for dashboard and reports
- MySQL/MariaDB production validation
- Error handling and audit completeness
- Performance checks for large event volumes

## Implementation Standards

1. Put business logic in services.
2. Use class-based views for CRUD and workflows.
3. Keep templates presentation-only.
4. Use reusable partials for filters, badges, tables, and summary cards.
5. Add audit logs for all important state changes.
6. Use atomic transactions for write operations.
7. Recalculate all summaries from source records.
8. Never allow direct manual stock mutation.

## Testing Strategy

Coverage should include:

- Model constraints
- Service calculations
- Permission boundaries
- Dashboard totals
- Inventory transaction integrity
- Report generation
- Import validation

Recommended test layers:

- Unit tests for business rules
- Integration tests for workflow transitions
- Permission tests for each role
- Regression tests for the Item Control Center summaries

## Assumptions

- One organization manages multiple events.
- The first release focuses on operational ERP workflows, not public donor portals.
- Event-level data isolation is mandatory from the start.
- PythonAnywhere remains the deployment target, but GitHub and local development remain the primary workflow.

