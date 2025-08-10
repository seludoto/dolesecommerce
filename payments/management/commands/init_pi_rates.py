from django.core.management.base import BaseCommand
from django.conf import settings
from decimal import Decimal
from payments.models import PiCoinRate

class Command(BaseCommand):
    help = 'Initialize Pi coin exchange rates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rate',
            type=float,
            default=0.314159,
            help='Pi to USD exchange rate (default: 0.314159)'
        )
        parser.add_argument(
            '--source',
            type=str,
            default='manual',
            help='Rate source (default: manual)'
        )

    def handle(self, *args, **options):
        rate = Decimal(str(options['rate']))
        source = options['source']
        
        # Deactivate existing rates
        PiCoinRate.objects.filter(is_active=True).update(is_active=False)
        
        # Create new rate
        pi_rate = PiCoinRate.objects.create(
            pi_to_usd=rate,
            source=source,
            is_active=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized Pi rate: 1 π = ${rate} USD (source: {source})'
            )
        )
