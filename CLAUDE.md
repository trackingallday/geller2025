

## Code Style Guidelines
- **Python**: Follow PEP 8 style guide with Django conventions
- **JavaScript**: Use ES6+ syntax with React functional components
- **Imports**: Group imports as: standard library, third-party, local applications
- **Naming**: Use descriptive variable/function names in camelCase (JS) or snake_case (Python)
- **Django Models**: Define `__str__` method for all models
- **Error Handling**: Use try/except in Python, try/catch in JavaScript with specific error types
- **Component Structure**: Group related components in directories with their CSS files
- **Comments**: Document complex logic and component props
- **Testing**: Write tests for all new features and critical components

##Always use skill
always load the simple-english skill and always use it

## Local dev server and login

CAUTION: The default `settings.py` database is the Railway **production**
postgres. Always give a settings module for local work.

Start the server on the local `geller1` database:

```
.venv/bin/python manage.py runserver 8912 --settings=chemicaldatasheets.settings_dev
```

Run the tests. `manage.py` switches to `settings_test.py` by itself:

```
.venv/bin/python manage.py test --noinput
```

Use the project virtualenv `.venv`. The global Python has a broken `pytz`.

### Dev staff login

This account is for the local dev database only. It does not exist in
production. Make it again with the command below if the database is reset.

- Username: `uitest`
- Password: `uitest-pw-12345`

```
.venv/bin/python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE']='chemicaldatasheets.settings_dev'
django.setup()
from django.contrib.auth.models import User
u, _ = User.objects.get_or_create(username='uitest')
u.is_staff = True
u.is_superuser = True
u.set_password('uitest-pw-12345')
u.save()
"
```

Sign in at `/admin/login/`, then open `/product-dashboard/`.
