#!/bin/sh
set -e

echo "Waiting for database to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "Database is ready - running migrations"
python manage.py migrate --noinput

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Starting Gunicorn"
exec "$@"
