import uuid
from django.db import models

from apps.base.models import BaseModel, BaseModelWithUser
from apps.shops.models import Shop, ShopCategory
from apps.users.models import User
from constants.currency_choices import CURRENCY_CHOICES
from .utils.generate_image_path import product_image_upload_path
from ..unit.models import Unit


class ProductGroup(BaseModelWithUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="product_groups", verbose_name="Shop")

    position = models.IntegerField("Position", default=0)

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Product Groups"

    def __str__(self):
        return str(self.pk)


class Product(BaseModelWithUser):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products", verbose_name="Shop")
    name = models.CharField(
        "Name", max_length=256,
    )
    description = models.TextField("Description", max_length=1000, )
    category = models.ForeignKey(ShopCategory, on_delete=models.CASCADE, verbose_name="Category")
    is_selected = models.BooleanField("Selected", default=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    sale_price = models.DecimalField("Sale Price", max_digits=50, decimal_places=5)
    barcode = models.CharField("Barcode", max_length=100, unique=True)
    is_active = models.BooleanField("Active", default=True)
    discount = models.DecimalField("Discount", max_digits=50, decimal_places=5)
    position_number = models.IntegerField("Position", default=0)
    group = models.ForeignKey(
        ProductGroup, on_delete=models.CASCADE,
        related_name="products", verbose_name="Group",
        null=True, blank=True
    )
    currency_type = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["position_number", ]

    def __str__(self):
        return self.name + " -- " + self.shop.name[:15]

    def __int__(self) -> int:
        return int(self.pk)


class ProductImage(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Product",
        null=True,
        blank=True
    )
    image = models.ImageField("Product Image", upload_to=product_image_upload_path)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ("order",)

    def __str__(self):
        return f"Image of {self.product.name if self.product else 'Unknown Product'}"


class ReportOption(models.Model):
    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="options", verbose_name="Parent",
                               null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.CharField(max_length=200, verbose_name="Description", null=True, blank=True)

    def __str__(self):
        return self.title


class Report(models.Model):
    report_option = models.ForeignKey(ReportOption, on_delete=models.CASCADE, related_name="reports",
                                      verbose_name="Report")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports", verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reports", verbose_name="Product")
    comment = models.TextField(max_length=1000, verbose_name="Comment")

    def __str__(self):
        return f"{self.user} -> {self.product} -> {self.comment}"
