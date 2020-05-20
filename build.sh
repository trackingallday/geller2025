#!/bin/bash
set -e # Fail fast
[ "$DEBUG" == 'true' ] && set -x # Print all commands

echo "Installing dependencies"
( cd marketing_front && npm i --no-package-lock)
( cd frontend && npm i --no-package-lock)

echo "Building React apps"
rm -rf marketing_front/build
yarn --cwd marketing_front build
rm -rf frontend/build
yarn --cwd frontend build

echo "Collecting Static Files"
(
    source ./.venv/bin/activate &&
    rm -rf dist_static/ &&
    python manage.py collectstatic --noinput
)