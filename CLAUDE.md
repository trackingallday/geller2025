# Geller Website - Development Guide

## ⚠️ Database & Settings — READ FIRST
- The default `chemicaldatasheets/settings.py` connects to the **Railway PRODUCTION database**. Never run `migrate`, `shell`, `runserver`, or any custom management command with the default settings on a dev machine.
- For ALL local manage.py commands, pass the local settings file: `--settings=chemicaldatasheets.settings_dev` (gitignored; local postgres `geller1`). Or `export DJANGO_SETTINGS_MODULE=chemicaldatasheets.settings_dev` once per shell.
- `python manage.py test` is the one exception — manage.py auto-switches to `chemicaldatasheets.settings_test` (local `geller_test` / test DB `test_geller`).
- Local postgres server is **Postgres.app v14** (data dir `~/Library/Application Support/Postgres/var-14`); the Homebrew postgres installs on this machine are stale — don't start them.

## Build Commands
- Setup virtual environment: `python3 -m venv .venv && source ./.venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt && cd marketing_front && npm i && cd ../frontend && npm i`
- Build React apps: `./build.sh`
- Start Django dev server: `python manage.py runserver --settings=chemicaldatasheets.settings_dev`
- Start React dev server: `cd marketing_front && npm start` or `cd frontend && npm start`
- Run tests: `python manage.py test`
- Run single test: `python manage.py test chemsapp.tests.TestClassName.test_method_name`
- Collect static files: `python manage.py collectstatic --noinput`
- Database migrations (local): `python manage.py makemigrations && python manage.py migrate --settings=chemicaldatasheets.settings_dev`
- Import dilution data (local): `python manage.py import_dilutions <xlsx> --dry-run --settings=chemicaldatasheets.settings_dev`

## Code Style Guidelines
- **Python**: Follow PEP 8 style guide with Django conventions
- **JavaScript**: Use ES6+ syntax with React functional components
- **React**: Component files use PascalCase, others use camelCase
- **Imports**: Group imports as: standard library, third-party, local applications
- **Naming**: Use descriptive variable/function names in camelCase (JS) or snake_case (Python)
- **Django Models**: Define `__str__` method for all models
- **Error Handling**: Use try/except in Python, try/catch in JavaScript with specific error types
- **Component Structure**: Group related components in directories with their CSS files
- **Comments**: Document complex logic and component props
- **Testing**: Write tests for all new features and critical components

## Repository Structure
- `/frontend` and `/marketing_front`: React applications
- `/chemsapp`: Django application code
- `/chemicaldatasheets`: Django project settings

##Always use skill
always load the simple-english skill and always use it
