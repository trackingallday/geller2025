from django.core.management.base import BaseCommand
from django.db import transaction

from quotes.models import Quote
from quotes.services import refresh_line_snapshots
from quotes.utils import QuotePDFGenerator


class Command(BaseCommand):
    help = (
        'Re-freeze the snapshotted fields on every quote line from current product data, '
        'then regenerate each changed PDF. Use this after a change to DESCRIPTION_MAX_CHARS '
        'or to the source fields, so that old proposals show the new text. '
        'CAUTION: this changes proposals that customers may already have.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would change, then roll back. No PDF is regenerated.',
        )
        parser.add_argument(
            '--quote-id', type=int, action='append', dest='quote_ids',
            help='Limit the run to this quote id. Repeat the flag for more than one quote.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        quotes = Quote.objects.all().order_by('id')
        if options['quote_ids']:
            quotes = quotes.filter(id__in=options['quote_ids'])

        changed = []
        with transaction.atomic():
            for quote in quotes:
                before = self._descriptions(quote)
                refresh_line_snapshots(quote)
                after = self._descriptions(quote)
                if before != after:
                    changed.append((quote, before, after))
            if dry_run:
                transaction.set_rollback(True)

        self._report(changed, quotes.count(), dry_run)

        if dry_run or not changed:
            return

        # PDFs are regenerated outside the transaction, so that one failure
        # does not roll back the snapshot data of every other quote.
        failed = []
        for quote, _before, _after in changed:
            try:
                QuotePDFGenerator(quote).generate_and_save()
            except Exception as exc:
                failed.append((quote, exc))
        self._report_pdfs(len(changed) - len(failed), failed)

    def _descriptions(self, quote):
        """Line id → description, read fresh from the database."""
        return dict(quote.lines.values_list('id', 'description'))

    def _report(self, changed, total, dry_run):
        write = self.stdout.write
        write(f'Quotes read: {total}')
        write(f'Quotes with a changed description: {len(changed)}')
        for quote, before, after in changed:
            write(f'  # {quote.quote_number}')
            for line_id, new_text in after.items():
                old_text = before.get(line_id, '')
                if old_text != new_text:
                    write(f'    line {line_id}: {len(old_text)} chars -> {len(new_text)} chars')
        if dry_run:
            write(self.style.WARNING('Dry run — all changes rolled back. No PDF was regenerated.'))

    def _report_pdfs(self, ok_count, failed):
        write = self.stdout.write
        write(self.style.SUCCESS(f'PDFs regenerated: {ok_count}'))
        if failed:
            write(self.style.ERROR(f'PDFs that failed ({len(failed)}):'))
            for quote, exc in failed:
                write(f'  ! {quote.quote_number}: {exc}')
