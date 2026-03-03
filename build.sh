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

echo "Checking for pending migrations..."
python manage.py makemigrations --check --dry-run

echo "Running database migrations..."
python manage.py migrate --noinput --verbosity 2

echo "Verifying database setup..."
python manage.py check --database default

echo "============================================"
echo "Build completed successfully!"
echo "============================================"