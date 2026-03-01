import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker

from apps.currency_rate.models import CurrencyRate
# Models
from apps.role_manager.models import Role
from apps.users.models import User as user_model
from apps.shops.models import Shop, ShopBalance
from apps.unit.models import Unit
from apps.products.models import Category, Product, ProductGroup

User = get_user_model()
fake = Faker()


def generate_uz_phone():
    """Generates a random unique phone number in +998XXXXXXXXX format."""
    # Common codes: 90, 91, 93, 94, 95, 97, 98, 99, 33, 77
    code = random.choice(['90', '91', '93', '94', '95', '97', '98', '99', '33', '77', '88'])
    number = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"+998{code}{number}"


class Command(BaseCommand):
    help = 'Seeds Shops with specific Member-to-Role logic and Currency Rates'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🧹 Cleaning Database...'))
        CurrencyRate.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Role.objects.all().delete()
        Shop.objects.all().delete()
        user_model.objects.exclude(is_superuser=True).delete()
        Unit.objects.all().delete()

        # 1. ROOT DATA
        admin_user, _ = user_model.objects.get_or_create(
            phone="admin",
            defaults={"is_staff": True, "is_superuser": True}
        )
        admin_user.set_password("admin123")
        admin_user.save()
        unit, _ = Unit.objects.get_or_create(name="pcs")

        # 2. CREATE 50 TOTAL USERS
        all_users = []
        for _ in range(50):
            u = user_model.objects.create(phone=generate_uz_phone(), first_name=fake.first_name())
            u.set_password("password123")
            u.save()
            all_users.append(u)

        # 3. CREATE SHOPS
        category_list = ['Electronics', 'Home', 'Grocery', 'Fashion']

        for i in range(5):
            shop = Shop.objects.create(
                name=f"Shop {i + 1}: {fake.company()}",
                description=fake.catch_phrase(),
                latitude="41.31", longitude="69.24"
            )

            # --- ADDING CURRENCY RATE FOR SHOP ---
            # Generates a rate around 12,800 - 12,900
            CurrencyRate.objects.create(
                user=admin_user,
                shop=shop,
                rate=Decimal(random.uniform(12800, 12900)).quantize(Decimal('0.00001'))
            )

            # MEMBERSHIP & ROLES
            shop_members = random.sample(all_users, 5)
            for member in shop_members:
                shop.members.add(member)
                Role.objects.create(
                    user=member,
                    shop=shop,
                    role=random.choice(['cashier_admin', 'owner']).lower(),
                    salary=Decimal('3500000.00'),
                    created_by=admin_user
                )

            # CATEGORIES & PRODUCTS
            cat_name = random.choice(category_list)
            category, _ = Category.objects.get_or_create(name=cat_name, defaults={'user': admin_user})
            category.shops.add(shop)
            group = ProductGroup.objects.create(shop=shop, user=admin_user)

            for p in range(10):  # Increased to 10 products per shop
                # RANDOM CURRENCY LOGIC
                currency = random.choice(['usd', 'uzs'])

                if currency == 'usd':
                    # Prices between $1.00 and $500.00
                    price = Decimal(random.uniform(1, 500)).quantize(Decimal('0.00001'))
                else:
                    # Prices between 10,000 and 2,000,000 UZS
                    price = Decimal(random.randint(10000, 2000000))

                Product.objects.create(
                    shop=shop,
                    user=admin_user,
                    category=category,
                    unit=unit,
                    group=group,
                    name=f"{cat_name} {fake.word().capitalize()}",
                    sale_price=price,
                    discount=Decimal('0.0'),
                    barcode=fake.unique.ean13(),
                    currency_type=currency,
                )

        self.stdout.write(self.style.SUCCESS('🎯 Master Seed Complete! Currency rates and mixed pricing added.'))
