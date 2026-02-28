import os
from django.core.management.base import BaseCommand
from chemsapp.views import downscale_image

DOCUMENTS_DIR = '/data/documents'


class Command(BaseCommand):
    help = 'Downscale all existing images in /data/documents in-place'

    def handle(self, *args, **options):
        if not os.path.isdir(DOCUMENTS_DIR):
            self.stderr.write(f'Directory not found: {DOCUMENTS_DIR}')
            return

        files = os.listdir(DOCUMENTS_DIR)
        changed = skipped = errors = 0

        for fname in files:
            fpath = os.path.join(DOCUMENTS_DIR, fname)
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
