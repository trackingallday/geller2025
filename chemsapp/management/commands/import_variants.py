from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from chemsapp.variants_import import import_variants_workbook


class Command(BaseCommand):
    help = (
        'Import product variants from the variants spreadsheet (Website ID / Code / '
        'Product / Size / Pack Size / Description / Barcode). Variants whose code '
        'already exists are skipped; missing Sizes are created with a parsed volume.'
    )

    def add_arguments(self, parser):
        parser.add_argument('xlsx_path', help='Path to the variants xlsx file')
        parser.add_argument('--dry-run', action='store_true', help='Report what would change, then roll back')

    def handle(self, *args, **options):
        with transaction.atomic():
            try:
                stats = import_variants_workbook(options['xlsx_path'])
            except FileNotFoundError:
                raise CommandError(f"File not found: {options['xlsx_path']}")
            if options['dry_run']:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING('Dry run — all changes rolled back.'))

        write = self.stdout.write
        write(f"Variants created: {len(stats['created'])}")
        write(f"Skipped (already exist): {len(stats['skipped_existing'])}")
        if stats['created_sizes']:
            write(self.style.SUCCESS(f"Sizes created ({len(stats['created_sizes'])}):"))
            for line in stats['created_sizes']:
                write(f'  + {line}')
        if stats['duplicate_codes']:
            write(self.style.WARNING(f"Duplicate codes in sheet ({len(stats['duplicate_codes'])}):"))
            for line in stats['duplicate_codes']:
                write(f'  ! {line}')
        if stats['unknown_products']:
            write(self.style.WARNING(f"Unknown products ({len(stats['unknown_products'])}):"))
            for line in stats['unknown_products']:
                write(f'  ? {line}')
