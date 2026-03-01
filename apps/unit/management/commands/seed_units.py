from django.core.management.base import BaseCommand
from apps.unit.models import Unit


class Command(BaseCommand):
    help = 'Seeds the database with default Measurement Units'

    def handle(self, *args, **kwargs):
        # List of units you want to ensure exist
        units_to_create = ['kg', 'dona', 'metr', 'litr', 'gramm']

        self.stdout.write(self.style.NOTICE('Starting unit seeding...'))

        created_count = 0
        for name in units_to_create:
            # get_or_create returns a tuple: (object, created_bool)
            unit, created = Unit.objects.get_or_create(name=name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created unit: "{name}"'))
                created_count += 1
            else:
                self.stdout.write(f'Unit "{name}" already exists. Skipping...')

        self.stdout.write(self.style.SUCCESS(f'Seeding complete! Added {created_count} new units.'))