#!/bin/bash
set -e # Fail fast
[ "$DEBUG" == 'true' ] && set -x # Print all commands

# Create virtual env if it doesn't exist
[ ! -d .venv ] && python3 -m venv .venv

echo "Installing python dependencies"
(
    source ./.venv/bin/activate &&
    pip install -r requirements.txt
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
