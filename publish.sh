#!/bin/bash
set -e # Fail fast
[ "$DEBUG" == 'true' ] && set -x # Print all commands

# Create a dist folder with everything required to run this application on a webserver.
# Only the dist folder will need to be deployed.

# Remove and recreate the dist folder.
echo "Preparing directories..."
rm -rf ./dist
mkdir ./dist

# Run a full build
echo "Building..."
./build.sh

echo "Adding scripts..."
cp deploy.sh requirements.txt manage.py ./dist
echo "Adding directories..."
cp -r chemicaldatasheets chemsapp dist_static apache ./dist
echo "Adding frontends..."
cp --parents marketing_front/build/*.* ./dist
cp --parents frontend/build/*.* ./dist
echo "Cleaning output..."
# Remove pycache/pyo/pyc files.
find ./dist | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf