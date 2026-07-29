#!/bin/sh
set -e

echo "======================================"
echo "Starting Django Application"
echo "======================================"

# Ensure staticfiles, static, and media directories exist
mkdir -p /app/staticfiles /app/static /app/media

echo "Waiting for database to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ Database is ready"

echo "Running migrations..."
if python manage.py migrate --noinput; then
  echo "✓ Migrations completed successfully"
else
  echo "✗ Migrations failed"
  exit 1
fi

echo "Collecting static files..."
if python manage.py collectstatic --noinput; then
  echo "✓ Static files collected successfully"
else
  echo "✗ Static file collection failed"
  exit 1
fi

echo "Starting Gunicorn..."
echo "======================================"
exec "$@"
