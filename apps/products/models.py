import sys
from decimal import Decimal
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from apps.base.models import BaseModel, BaseModelWithUser
from apps.shops.models import Shop
from apps.unit.models import Unit
from apps.users.models import User
from constants.currency_choices import CURRENCY_CHOICES
from .utils.generate_image_path import product_image_upload_path


class ProductGroup(BaseModelWithUser):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="product_groups", verbose_name="Shop")
    position = models.IntegerField("Position", default=0)

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Product Groups"

    def __str__(self):
        return str(self.pk)


class Category(BaseModelWithUser):
    name = models.CharField("Name", max_length=256)
    shops = models.ManyToManyField(
        Shop,
        related_name="categories",
        verbose_name="Shops",
        blank=True,
    )
    image = models.ImageField("Image", upload_to="shop-category-images/",
                              default="shop-category-images/default-image.png")
    can_delete = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(BaseModelWithUser):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products", verbose_name="Shop")
    name = models.CharField(
        "Name", max_length=256,
    )
    description = models.TextField("Description", max_length=1000, )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="Category",
        blank=True, null=True, related_name="products"
    )
    is_selected = models.BooleanField("Selected", default=False)
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE,
        blank=True, null=True, related_name="products"
    )
    sale_price = models.DecimalField("Sale Price", max_digits=50, decimal_places=5)
    barcode = models.CharField("Barcode", max_length=100, unique=True)
    is_active = models.BooleanField("Active", default=True)
    discount = models.DecimalField("Discount", max_digits=50, decimal_places=5, default=Decimal("0"))
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

    def save(self, *args, **kwargs):
        # 1. Check if there is an image and if it's a new file being uploaded
        if self.image and (not self.pk or self._image_changed()):
            self.image = self.compress_image(self.image)

        super().save(*args, **kwargs)

    def _image_changed(self):
        """Checks if the image file has actually changed to avoid re-compressing."""
        old_obj = ProductImage.objects.filter(pk=self.pk).first()
        return old_obj.image != self.image if old_obj else True

    def compress_image(self, uploaded_image):
        img = Image.open(uploaded_image)

        # 2. Fix Orientation: Prevent the photo from rotating
        img = ImageOps.exif_transpose(img)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        output = BytesIO()
        quality = 90

        # 3. Targeted Compression Loop
        while True:
            output.seek(0)
            output.truncate(0)
            img.save(output, format='JPEG', quality=quality)

            file_size = output.tell()

            # Target: Stop if under 500KB or if quality gets too low
            # 512000 bytes = 500 KB
            if file_size <= 512000 or quality <= 20:
                break
            quality -= 5

        output.seek(0)
        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{self.image.name.split('.')[0]}.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )

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
