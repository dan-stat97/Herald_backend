#!/usr/bin/env bash
# exit on error
set -o errexit

echo "============================================"
echo "Herald Backend - Build Process"
echo "============================================"

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running database migrations (safe mode)..."
python manage.py migrate_safe

echo "Verifying database setup..."
python manage.py check --database default

echo "============================================"
echo "Build completed successfully!"
echo "============================================"