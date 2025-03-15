# Geller Website - Development Guide

## Build Commands
- Setup virtual environment: `python3 -m venv .venv && source ./.venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt && cd marketing_front && npm i && cd ../frontend && npm i`
- Build React apps: `./build.sh`
- Start Django dev server: `python manage.py runserver`
- Start React dev server: `cd marketing_front && npm start` or `cd frontend && npm start`
- Run tests: `python manage.py test`
- Run single test: `python manage.py test chemsapp.tests.TestClassName.test_method_name`
- Collect static files: `python manage.py collectstatic --noinput`
- Database migrations: `python manage.py makemigrations && python manage.py migrate`

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