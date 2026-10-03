import tempfile

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'geller_test',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_geller',
        },
    }
}

# settings.py hardcodes MEDIA_ROOT to the production Railway volume ('/data'),
# which doesn't exist on a dev machine or CI. Tests that write files (PDFs,
# uploaded photos) need a real, writable directory.
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'geller_test_media')
