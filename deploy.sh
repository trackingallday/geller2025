#!/bin/bash
# My first script

echo "Building Javascripts"


./deploy_marketing.sh &&
./deploy_bakend.sh &&

echo "Activating Venv"

source ./.venv/bin/activate &&

echo "Collecting Static Files"

python manage.py collectstatic --noinput &&

echo "Migrating"

python manage.py makemigrations &&
python manage.py migrate &&

echo "Restarting Apache"

# service Apache2 restart &&

echo "Done"
