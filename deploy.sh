#!/bin/bash
set -e # Fail fast
[ "$DEBUG" == 'true' ] && set -x # Print all commands

./build.sh

echo "Collecting Static Files"
(
    source ./.venv/bin/activate &&
    rm -rf dist_static/ &&
    python manage.py collectstatic --noinput
)

echo "Migrating"
(
    source ./.venv/bin/activate &&
    python manage.py makemigrations &&
    python manage.py migrate
)

echo "Restarting Apache"
service apache2 restart

echo "Done"
