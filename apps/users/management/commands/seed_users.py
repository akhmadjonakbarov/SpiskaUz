from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with initial users'

    def handle(self, *args, **kwargs):
        # Define the users you want to create
        users_to_create = [
            {
                "phone": "+998901234567",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True
            },
            {
                "phone": "+998909876543",
                "first_name": "John",
                "last_name": "Doe",
                "is_staff": False,
            },
        ]

        self.stdout.write(self.style.NOTICE('Starting user seeding...'))

        for user_data in users_to_create:
            phone = user_data.get("phone")

            # Use get_or_create based on the unique phone number
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "is_staff": user_data.get("is_staff", False),
                    "is_superuser": user_data.get("is_superuser", False),
                }
            )

            if created:
                # IMPORTANT: Set a password and save
                user.set_password("password123")
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {phone}'))
            else:
                self.stdout.write(f'User {phone} already exists. Skipping...')

        self.stdout.write(self.style.SUCCESS('User seeding complete!'))