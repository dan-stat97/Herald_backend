#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking for pending migrations..."
python manage.py makemigrations --check --dry-run

echo "Running migrations..."
python manage.py migrate --noinput

echo "Verifying database setup..."
python manage.py check --database default

echo "Build completed successfully!"