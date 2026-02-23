import uuid

from django.db import models

from apps.products.models import Product
from apps.shops.models import Shop


class CashPaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"


class CashHistory(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="cash_history", verbose_name="Shop")
    payment_method = models.CharField(max_length=10, choices=CashPaymentMethod.choices, default=CashPaymentMethod.CASH)
    comment = models.TextField(verbose_name="Comment", null=True, blank=True)

    class Meta:
        verbose_name = "Cash History"
        verbose_name_plural = "Cash Histories"

    def __str__(self):
        return f"{self.shop}->{self.payment_method}->{self.comment}"


class CashHistoryItem(models.Model):
    cash_history = models.ForeignKey(CashHistory, on_delete=models.CASCADE, related_name="cash_history_item", verbose_name="Cash History")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cash_history_item", verbose_name="Product")
    amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Amount")
    sale_price = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Sale Price")
    discount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Discount", default=0)
    product_price = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Product Price")

    class Meta:
        verbose_name = "Cash History Item"
        verbose_name_plural = "Cash History Items"

    def __str__(self):
        return f"{self.cash_history}->{self.product.name}"
