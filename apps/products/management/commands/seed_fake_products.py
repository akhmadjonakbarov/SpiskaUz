import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.unit.models import Unit
from apps.shops.models import Shop
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seeds Categories and Products'

    def handle(self, *args, **options):
        # 1. Get basic dependencies
        user = User.objects.first()
        shop = Shop.objects.first()
        unit = Unit.objects.first()

        if not all([user, shop, unit]):
            self.stdout.write(self.style.ERROR('Seed Users, Shops, and Units first!'))
            return

        # 2. Create Categories
        category_names = ['Electronics', 'Groceries', 'Home Decor', 'Fashion', 'Sports']
        categories = []

        self.stdout.write(self.style.NOTICE('Seeding Categories...'))
        for name in category_names:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'user': user, 'can_delete': True}
            )
            # ManyToMany link to Shop
            category.shops.add(shop)
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Category "{name}" created.'))

        # 3. Create Products
        self.stdout.write(self.style.NOTICE('Seeding 20 Products...'))
        for _ in range(20):
            price = random.randint(10, 1000)

            product = Product.objects.create(
                user=user,
                shop=shop,
                category=random.choice(categories),
                unit=unit,
                name=fake.word().capitalize() + " " + fake.word(),
                description=fake.text(max_nb_chars=200),
                sale_price=price,
                discount=price * 0.1,  # 10% discount
                barcode=fake.unique.ean13(),
                currency_type='UZS',  # Replace with your choice (e.g., 'USD')
                is_active=True,
                position_number=random.randint(1, 100)
            )
            self.stdout.write(self.style.SUCCESS(f'Product "{product.name}" added.'))

        self.stdout.write(self.style.SUCCESS('Seeding finished successfully!'))