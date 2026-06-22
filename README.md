# KMM Chaturmas ERP

Production-grade Django ERP for Kalyan Mitra Mandal Chaturmas operations.

## Status

Phase 3 implementation is in place with reporting, analytics, export tooling, seed data, deployment workflow, and operational scripts.

## Design Principles

- Every record belongs to an event.
- Inventory is ledger-based and never edited manually.
- Calculations are derived from source transactions.
- Business logic lives in services.
- The UI is Bootstrap 5 and mobile-first.

## Setup

1. Create and activate a Python 3.12 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local `.env` file from `.env.example`.
4. Run migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Bootstrap access accounts:

```bash
python manage.py bootstrap_access --systemadmin-password "change-me" --admin-password "change-me" --viewer-password "change-me"
```

7. Load sample data after importing standard items:

```bash
python manage.py import_standard_items --replace
python manage.py seed_sample_data --replace
```

8. Run the development server:

```bash
python manage.py runserver
```

## Deployment Notes

- Development uses SQLite.
- Production should switch to MySQL or MariaDB through environment variables.
- PythonAnywhere deployment instructions are in `deployment/pythonanywhere.md`.
- GitHub Actions CI is defined in `.github/workflows/django-ci.yml`.
- Event snapshots can be exported with `python manage.py export_event_snapshot`.
- A standalone account bootstrap helper is available at `deployment/create_admin_user.py`.

## Localization

The UI is English-first with a site-wide Gujarati toggle available in the top bar.
