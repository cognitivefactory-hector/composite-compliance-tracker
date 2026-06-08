#!/usr/bin/env bash
set -euo pipefail

# Apply DB migrations, then collect static assets (whitenoise serves them).
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Optional: load the synthetic shop so the public demo is never empty. Only
# seeds when the DB has no criteria yet, so restarts don't wipe a persistent DB.
if [ "${SEED_ON_START:-false}" = "true" ]; then
  python manage.py seed_shop --if-empty
fi

exec "$@"
