#!/bin/bash
set -e # Fail fast
[ "$DEBUG" == 'true' ] && set -x # Print all commands

./build.sh

echo "Migrating"
(
    source ./.venv/bin/activate &&
    python manage.py makemigrations &&
    python manage.py migrate
)

echo "Restarting Apache"
service apache2 restart

echo "Done"
