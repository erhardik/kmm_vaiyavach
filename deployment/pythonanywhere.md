# PythonAnywhere Deployment

1. Clone or pull the repository from GitHub.
2. Install Python dependencies.

```bash
pip install -r requirements.txt
```

3. Apply database migrations.

```bash
python manage.py migrate
```

4. Collect static files when production static handling is enabled.

```bash
python manage.py collectstatic --noinput
```

5. Reload the PythonAnywhere web app.

## Environment Variables

- `DJANGO_ENV=production`
- `SECRET_KEY`
- `DEBUG=0`
- `ALLOWED_HOSTS`
- `DB_ENGINE=django.db.backends.mysql`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

