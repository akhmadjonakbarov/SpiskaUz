from django.db import models
from django.utils import timezone

from apps.base.models import BaseModelWithUserAndShop, PriceAndQtyMixinWithPercentage
from apps.currency_rate.models import CurrencyRate
from apps.products.models import Product
from apps.supplier.models import Supplier
from apps.users.models import User


class ProductPart(BaseModelWithUserAndShop, PriceAndQtyMixinWithPercentage):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="parts")
    currency_rate = models.ForeignKey(
        CurrencyRate, on_delete=models.SET_NULL, blank=True, null=True
    )
    currency_rate_value = models.DecimalField(
        blank=True, null=True, max_digits=50, decimal_places=5
    )
    confirmed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="confirmed_by", blank=True, null=True
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    is_confirm = models.BooleanField(
        default=False
    )

    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, related_name="product_parts", blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Product Part"
        verbose_name_plural = "Product Parts"

    def __str__(self) -> str:
        return f"{self.product.name} {self.qty}"

    def confirm(self, user: User, supplier: Supplier):
        self.supplier = supplier
        self.is_confirm = True
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()
        return self
