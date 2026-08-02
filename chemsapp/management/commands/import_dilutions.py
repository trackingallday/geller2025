from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from chemsapp.dilutions_import import import_dilutions_workbook


class Command(BaseCommand):
    help = (
        'Import dilution options from the "Dilutions for Geller" spreadsheet. '
        'Seeds ApplicationTypes from the sheet columns, matches each row\'s SKU to a '
        'ProductVariant (falling back to Product.productCode) and syncs its DilutionVariant rows.'
    )

    def add_arguments(self, parser):
        parser.add_argument('xlsx_path', help='Path to the Dilutions xlsx file')
        parser.add_argument('--dry-run', action='store_true', help='Report what would change, then roll back')
        parser.add_argument(
            '--create-missing-variants', action='store_true',
            help='Create a ProductVariant for rows whose SKU is unknown but whose product can be matched '
                 'by productCode or exact name',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            try:
                stats = import_dilutions_workbook(
                    options['xlsx_path'],
                    create_missing_variants=options['create_missing_variants'],
                )
            except FileNotFoundError:
                raise CommandError(f"File not found: {options['xlsx_path']}")
            if options['dry_run']:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING('Dry run — all changes rolled back.'))

        self._report(stats)

    def _report(self, stats):
        write = self.stdout.write
        write(f"Matched variants: {len(stats['matched'])}")
        write(f"Dilution rows synced: {stats['dilutions']}")
        write(f"Size volumes backfilled: {stats['volume_backfills']}")
        if stats['created_variants']:
            write(self.style.SUCCESS(f"Created variants ({len(stats['created_variants'])}):"))
            for line in stats['created_variants']:
                write(f'  + {line}')
        if stats['duplicate_skus']:
            write(self.style.WARNING(f"Duplicate SKUs in sheet ({len(stats['duplicate_skus'])}):"))
            for line in stats['duplicate_skus']:
                write(f'  ! {line}')
        if stats['skipped_empty']:
            write(f"Rows with no dilution data (skipped): {len(stats['skipped_empty'])}")
        if stats['unmatched']:
            write(self.style.WARNING(f"Unmatched SKUs ({len(stats['unmatched'])}):"))
            for line in stats['unmatched']:
                write(f'  ? {line}')
