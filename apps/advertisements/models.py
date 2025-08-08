from django.db import models

from apps.shops.models import Shop
from apps.users.models import User


class AdvertisementCategory(models.Model):
    name = models.CharField("Name", max_length=256)
    image = models.ImageField("Image", upload_to="category-images/", default="category-images/default.jpg")

    class Meta:
        verbose_name = "Advertisement Category"
        verbose_name_plural = "Advertisement Categories"

    def __str__(self):
        return self.name


class Advertisement(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Shop")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ads", verbose_name="Owner")
    name = models.CharField("Name", max_length=128)
    description = models.TextField("Description", max_length=1000)
    category = models.ForeignKey(AdvertisementCategory, on_delete=models.CASCADE, related_name="ads", verbose_name="Category")
    price = models.IntegerField("Price")
    phone = models.CharField("Phone", max_length=15)
    status = models.CharField(
        "Status",
        choices=(
            ("YANGI", "Yangi"),
            ("ESKI", "Eski"),
        ),
        max_length=128,
    )
    published = models.BooleanField("Published", default=False)
    address = models.TextField("Address")
    latitude = models.CharField("Latitude", max_length=256)
    longitude = models.CharField("Longitude", max_length=256)
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"

    def __str__(self):
        return f"Advertisement(name={self.name}, price={self.price})"


class AdvertisementImage(models.Model):
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name="images", verbose_name="Advertisement", null=True, blank=True)
    image = models.ImageField("Image", upload_to="advertisement-images/")
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Advertisement Image"
        verbose_name_plural = "Advertisement Images"
