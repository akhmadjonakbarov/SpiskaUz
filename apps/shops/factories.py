import factory
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.shops.models import Shop


class ShopFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Shop

    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=200)
    latitude = "40.7128"
    longitude = "-74.0060"
    address = factory.Faker("address")
    telegram_link = factory.Faker("url")

    image = factory.LazyFunction(
        lambda: SimpleUploadedFile(
            name="shop.jpg",
            content=b"fake-image-content",
            content_type="image/jpeg",
        )
    )
