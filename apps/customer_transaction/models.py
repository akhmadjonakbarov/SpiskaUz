from decimal import Decimal
from django.db import models
from apps.base.models import BaseModelWithShop


class CustomerTransaction(BaseModelWithShop):
    TransactionType = (
        ('debt', 'Debt'),
        ('payment', 'Payment')
    )
    customer = models.ForeignKey(
        "users.User", verbose_name="Customer",
        on_delete=models.CASCADE,
        related_name="transactions_as_customer",
    )
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(
        max_digits=50, decimal_places=5,
    )
    currency_rate = models.DecimalField(
        max_digits=50, decimal_places=5, default=Decimal('0.0')
    )
    transaction_type = models.CharField(
        choices=TransactionType, blank=True, null=True, max_length=250
    )

    def __str__(self):
        return f"{self.customer} - Payment: {self.amount}"
