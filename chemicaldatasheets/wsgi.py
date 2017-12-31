"""
WSGI config for chemicaldatasheets project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os, sys

sys.path.append('/home/rimu/chemicaldatatapp')

sys.path.append('/home/rimu/chemicaldataapp/venv/lib/python3.6/site-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chemicaldatasheets.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
