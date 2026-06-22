# Deployment Guide

## Local Development

1. Install Python 3.12.
2. Create a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and edit values.
5. Run `python manage.py migrate`.
6. Run `python manage.py bootstrap_access`.
7. Optionally seed demo data with:

```bash
python manage.py import_standard_items --replace
python manage.py seed_sample_data --replace
```

## GitHub Workflow

- CI runs on pushes and pull requests via `.github/workflows/django-ci.yml`.
- The workflow installs dependencies, runs migrations, runs checks, and executes tests.

## PythonAnywhere

1. Clone the repository on PythonAnywhere.
2. Create a virtualenv for Python 3.12.
3. Install dependencies.
4. Set environment variables from `.env.example`.
5. Run migrations.
6. Collect static files.
7. Reload the web app.

## Backup and Export

- Use `python manage.py export_event_snapshot` to generate a CSV and JSON snapshot in `media/exports/`.
- Use the Reports screen for ad-hoc operational exports.
