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
    # We make migrations server side because we don't ship the database.
    python manage.py makemigrations &&
    python manage.py migrate
)

chown -R rimu:www-data .
chmod -R 755 ./chemsapp/media

echo "Restarting Apache"
service apache2 restart

echo "Done"
