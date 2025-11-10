#!/bin/sh
set -e

export DJANGO_SETTINGS_MODULE=config.settings.prod

echo "=== Clearing All Poetry Caches ==="
RUN /root/.local/bin/poetry install --no-interaction --no-ansi --no-root \
    && rm -rf /root/.cache/pypoetry/* \
    && rm -rf /root/.cache/pip/*

echo "=== Running Django migrations ==="
/root/.local/bin/poetry run python manage.py makemigrations --noinput || true
/root/.local/bin/poetry run python manage.py migrate --noinput

/root/.local/bin/poetry run python manage.py collectstatic --noinput

echo "=== Starting Gunicorn server ==="
/root/.local/bin/poetry run gunicorn --bind 0.0.0.0:8000 config.wsgi:application --workers 2