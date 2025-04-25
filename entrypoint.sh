#!/bin/bash
set -e

echo "making migrations..."
python manage.py makemigrations --noinput

echo "Running migrations..."
python manage.py migrate --noinput --fake-initial

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser..."
# Creates superuser only if it doesn't already exist
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'admin'
email = 'admin@example.com'
password = 'adminpass'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
END

echo "Starting Django server..."
exec "$@"
