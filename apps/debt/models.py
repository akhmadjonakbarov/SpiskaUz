from decimal import Decimal
from django.db import models

from apps.base.models import BaseModel


class DebtConversion(models.Model):
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="debt_conversions")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="debt_conversions")
    amount_uzs = models.DecimalField(max_digits=14, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, editable=False)
    converted_at = models.DateTimeField(auto_now_add=True)
    reverted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        rate = self.shop.usd_exchange_rate
        if not rate:
            raise ValueError("Shop USD kursi mavjud emas.")
        self.amount_usd = round(self.amount_uzs / rate, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} converted {self.amount_uzs} UZS to {self.amount_usd} USD @ {self.shop.name}"


class DebtPayment(models.Model):
    class Currency(models.TextChoices):
        UZS = "UZS", "So‘m"
        USD = "USD", "Dollar"

    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="debt_payments")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="debt_payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.UZS)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.amount} {self.currency} ({self.shop.name})"

    @property
    def amount_in_uzs(self):
        if self.currency == "UZS":
            return self.amount
        # Kursni shop'dan olish
        return round(self.amount * self.shop.usd_exchange_rate, 2)


class Debt(BaseModel):
    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="debts_created"
    )
    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="debts", blank=True, null=True
    )
    document = models.OneToOneField(
        "document.Document", on_delete=models.CASCADE, related_name="document"
    )
    client = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="debts_as_client"
    )
    paid_money = models.DecimalField(
        max_digits=50, decimal_places=5, default=Decimal('0.0')
    )
    is_accepted = models.BooleanField(
        default=False
    )
    is_paid = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.client} - {self.document.doc_type}"

    def accept(self):
        self.is_accepted = True
        self.save()
