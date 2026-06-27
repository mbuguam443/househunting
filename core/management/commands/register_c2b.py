from django.core.management.base import BaseCommand
from tenants.c2b_utils import register_c2b_urls


class Command(BaseCommand):
    help = 'Register C2B confirmation/validation URLs with Safaricom Daraja API'

    def handle(self, *args, **options):
        self.stdout.write('Registering C2B URLs with Safaricom...')
        result = register_c2b_urls()
        self.stdout.write(str(result))
        if result.get('ResponseCode') == '0':
            self.stdout.write(self.style.SUCCESS('C2B URLs registered successfully!'))
        else:
            self.stdout.write(self.style.WARNING('Registration may have failed. Check response above.'))
