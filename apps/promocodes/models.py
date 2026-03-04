from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from apps.base.models import BaseModel
from apps.products.models import Product
from apps.shops.models import Shop


class PromoCode(BaseModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="promocodes")
    code = models.CharField(max_length=256, unique=True, editable=True, validators=[
        RegexValidator(regex=r"^[A-Za-z0-9]+$",
                       message="Code faqat harf va raqamlardan tashkil topishi kerak. Bo'sh joyga ruxsat yo'q.")])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="promocode_created_by",
        null=True, blank=True
    )

    def __str__(self) -> str:
        return f"PromoCode({self.shop.id}, {self.code})"

    class Meta:
        unique_together = ["shop", "code"]

    def can_use_promo_code(self, user):
        return not self.usages.filter(user=user).exists()


class PromoCodeItem(models.Model):
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    class Meta:
        unique_together = ["promo_code", "product"]

    def __str__(self):
        return f"PromoCodeItem({self.product.name}, {self.discount})"


class PromoCodeUsage(models.Model):
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="promo_code_usages")
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PromoCodeUsage({self.promo_code.code}, {self.user.get_full_name()})"
