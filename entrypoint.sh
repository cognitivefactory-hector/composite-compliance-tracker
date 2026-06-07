#!/usr/bin/env bash
set -euo pipefail

# Apply DB migrations, then collect static assets (whitenoise serves them).
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
