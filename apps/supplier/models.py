from decimal import Decimal

from django.db import models

from apps.base.models import BaseModel, BaseModelWithUser
from apps.users.models import User


class Supplier(BaseModel):
    name = models.CharField(max_length=250)
    phone_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.name)


class SupplierDebtBalance(BaseModel):
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE, related_name='debt_balance')
    balance_usd = models.DecimalField(
        max_digits=50, decimal_places=5, default=Decimal('0.0')
    )
    balance_uzs = models.DecimalField(
        max_digits=50, decimal_places=5, default=Decimal('0.0')
    )

    def __str__(self):
        return self.supplier.name


class DebtPaymentHistory(BaseModel):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="debt_payment_histories"
    )
    balance = models.ForeignKey(SupplierDebtBalance, on_delete=models.CASCADE, related_name="histories")
    amount = models.DecimalField(
        max_digits=50, decimal_places=5,
    )
    currency_type = models.CharField(
        max_length=10,
    )
    currency_rate = models.DecimalField(
        max_digits=50, decimal_places=5, default=Decimal('0.0')
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.supplier.name} - Payment: {self.amount}"
