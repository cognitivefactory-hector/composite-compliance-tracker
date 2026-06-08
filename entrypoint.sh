#!/usr/bin/env bash
set -euo pipefail

# Apply DB migrations, then collect static assets (whitenoise serves them).
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Optional: (re)load the synthetic shop so the public demo always shows the
# intended state. The seed is idempotent and uses only synthetic data.
if [ "${SEED_ON_START:-false}" = "true" ]; then
  python manage.py seed_shop
fi

exec "$@"
