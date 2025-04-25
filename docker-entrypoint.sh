#!/bin/bash
set -e

# Create SQLite database for initial setup
echo "Setting up database..."
if [ "${POSTGRES_HOST}" = "localhost" ] || [ "${POSTGRES_HOST}" = "127.0.0.1" ]; then
  # Using SQLite configuration
  export DJANGO_SETTINGS_MODULE=chemicaldatasheets.settings
else
  # Using PostgreSQL configuration
  export DJANGO_SETTINGS_MODULE=chemicaldatasheets.settings_docker
fi

echo "Making migrations..."
python manage.py makemigrations --no-input

echo "Applying database migrations..."
python manage.py migrate --fake

# Create superuser if not exists
echo "Checking if superuser exists..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')
    )
    print(f'Superuser {username} created')
else:
    print(f'Superuser {username} already exists')
"

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn chemicaldatasheets.wsgi:application --bind 0.0.0.0:8000