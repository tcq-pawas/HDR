#!/bin/sh
set -e

echo "======================================"
echo "Starting Django Application"
echo "======================================"

# Ensure static/media directories exist (including common upload paths)
mkdir -p /app/staticfiles /app/static /app/media \
  /app/media/properties \
  /app/media/properties/featured \
  /app/media/properties/videos \
  /app/media/properties/videos/drone \
  /app/media/properties/floorplans \
  /app/media/properties/documents \
  /app/media/properties/documents/registry \
  /app/media/properties/documents/sale_deed \
  /app/media/properties/documents/mutation \
  /app/media/properties/documents/approval \
  /app/media/properties/documents/completion \
  /app/media/properties/documents/noc \
  /app/media/properties/documents/layout \
  /app/media/properties/documents/brochure \
  /app/media/agent_profiles \
  /app/media/agent_verification \
  /app/media/agent_verification/id_proof \
  /app/media/agent_verification/address_proof \
  /app/media/documents \
  /app/media/customer_profiles \
  /app/media/profile_images \
  /app/media/kyc_documents \
  /app/media/admin_profiles \
  /app/media/plan_badges \
  /app/media/investment_reports \
  /app/media/investor_documents

# Named Docker volumes are root-owned by default; fix so appuser can write uploads
if [ "$(id -u)" = "0" ]; then
  chown -R appuser:appuser /app/media /app/staticfiles /app/static
  echo "✓ Media/static volume permissions fixed"
fi

run_as_app() {
  if [ "$(id -u)" = "0" ]; then
    runuser -u appuser -- "$@"
  else
    "$@"
  fi
}

echo "Waiting for database to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ Database is ready"

echo "Running migrations..."
if run_as_app python manage.py migrate --noinput; then
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

if [ "$(id -u)" = "0" ]; then
  exec runuser -u appuser -- "$@"
else
  exec "$@"
fi
