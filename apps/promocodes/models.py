from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from apps.base.models import BaseModel
from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.models import User

class PromoCode(BaseModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="promocodes")
    code = models.CharField(max_length=256, unique=True, editable=True, validators=[
        RegexValidator(regex=r"^[A-Za-z0-9]+$",
                       message="Code faqat harf va raqamlardan tashkil topishi kerak. Bo'sh joyga ruxsat yo'q.")])
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"PromoCode({self.shop.id}, {self.code})"

    class Meta:
        unique_together = ["shop", "code"]

    def can_use_promocode(self, user):
        return not self.usages.filter(user=user).exists()


class PromocodeItem(models.Model):
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    class Meta:
        unique_together = ["promocode", "product"]

    def __str__(self):
        return f"PromocodeItem({self.product.name}, {self.discount})"


class PromocodeUsage(models.Model):
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="promocode_usages")
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PromocodeUsage({self.promocode.code}, {self.user.get_full_name()})"
