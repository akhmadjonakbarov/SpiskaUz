import random
from django.core.management.base import BaseCommand
from apps.shops.models import Shop
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generates 50 random shops for testing'

    def add_arguments(self, parser):
        # Allows you to run: python manage.py seed_fake_shops --total 100
        parser.add_argument('--total', type=int, default=50, help='Number of shops to create')

    def handle(self, *args, **options):
        total = options['total']

        # Get a random user to assign as a member
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('Create a user first!'))
            return

        self.stdout.write(self.style.NOTICE(f'Generating {total} fake shops...'))

        for _ in range(total):
            # Generate fake data
            name = f"{fake.company()} {fake.company_suffix()}"
            description = fake.paragraph(nb_sentences=3)
            address = fake.address()

            # Approximate coordinates for Tashkent region
            lat = str(random.uniform(41.2, 41.4))
            lon = str(random.uniform(69.1, 69.3))

            shop = Shop.objects.create(
                name=name,
                description=description,
                address=address,
                latitude=lat,
                longitude=lon,
                # Using a placeholder image or leaving it for the default/blank
                image="shop-images/default.png"
            )

            # Add the member
            shop.members.add(user)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {total} shops!'))