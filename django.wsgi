import os
import sys

path='/home/rimu/chemicaldataapp/'

if path not in sys.path:
  sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'chemicaldatasheets.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()



