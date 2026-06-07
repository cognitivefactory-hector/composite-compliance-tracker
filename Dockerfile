FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching. psycopg[binary] ships its
# own libpq, so no system build deps are required.
COPY pyproject.toml ./
COPY config ./config
COPY tracker ./tracker
RUN pip install --upgrade pip && pip install .

COPY manage.py ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Invoke via bash so a dev bind-mount that drops the exec bit can't break startup.
ENTRYPOINT ["bash", "entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
