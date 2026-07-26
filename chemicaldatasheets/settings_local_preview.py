# Throwaway settings for previewing pages locally without touching the
# Railway production database. Not used in deployment.
import tempfile

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'geller_preview',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

MEDIA_ROOT = tempfile.gettempdir() + '/geller_preview_media'
DEBUG = True
