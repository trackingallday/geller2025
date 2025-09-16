from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings
import sys
import json


class Command(BaseCommand):
    help = 'Send email asynchronously'

    def add_arguments(self, parser):
        parser.add_argument('--subject', type=str, required=True, help='Email subject')
        parser.add_argument('--body', type=str, required=True, help='Email body')
        parser.add_argument('--to', type=str, required=True, help='Recipient email')
        parser.add_argument('--from-email', type=str, help='Sender email (optional)')
        parser.add_argument('--reply-to', type=str, help='Reply-to email (optional)')

    def handle(self, *args, **options):
        try:
            msg = EmailMessage(
                subject=options['subject'],
                body=options['body'],
                from_email=options.get('from_email', settings.EMAIL_FROM),
                to=[options['to']],
            )
            
            if options.get('reply_to'):
                msg.reply_to = [options['reply_to']]
            
            msg.send(fail_silently=False)
            
            self.stdout.write(
                self.style.SUCCESS(f'Email sent successfully to {options["to"]}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {str(e)}')
            )
            sys.exit(1)