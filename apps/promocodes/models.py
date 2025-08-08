from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from apps.base.models import BaseModel
from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.models import User


class Promocode(BaseModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="shop_promocodes")
    user = models.ForeignKey(User, related_name="user_promocodes", on_delete=models.CASCADE)

    product = models.OneToOneField(Product, related_name="promo_code", on_delete=models.CASCADE)
    code = models.CharField(max_length=256, unique=True, editable=True, validators=[
        RegexValidator(regex=r"^[A-Za-z0-9]+$",
                       message="Code faqat harf va raqamlardan tashkil topishi kerak. Bo'sh joyga ruxsat yo'q.")])
    value = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return f"Promocode({self.shop.name}, {self.code})"


class PromocodeItem(models.Model):
    promocode = models.ForeignKey(Promocode, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    class Meta:
        unique_together = ["promocode", "product"]

    def __str__(self):
        return f"{self.product.name} - {self.discount}"


class PromocodeUsage(models.Model):
    promocode = models.ForeignKey(Promocode, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="promocode_usages")
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.promocode.code}, {self.user.get_full_name()}"
