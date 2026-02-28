import os
from django.conf import settings
from django.core.management.base import BaseCommand
from chemsapp.views import downscale_image


class Command(BaseCommand):
    help = 'Downscale all existing JPEG/PNG images in the documents directory in-place'

    def handle(self, *args, **options):
        documents_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
        if not os.path.isdir(documents_dir):
            self.stderr.write(f'Directory not found: {documents_dir}')
            return

        files = os.listdir(documents_dir)
        changed = skipped = errors = 0

        for fname in files:
            fpath = os.path.join(documents_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                result = downscale_image(fpath)
                if result:
                    changed += 1
                    self.stdout.write(f'  resized: {fname}')
                else:
                    skipped += 1
            except Exception as e:
                errors += 1
                self.stderr.write(f'  ERROR {fname}: {e}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Changed: {changed}, Skipped: {skipped}, Errors: {errors}'
            )
        )
