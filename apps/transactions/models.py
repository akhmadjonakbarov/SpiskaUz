from django.db import models

from apps.shops.models import Shop
from apps.users.models import User


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ("cash", "Naqd pul"),
        ("profit", "Foyda"),
        ("cash_and_profit", "Naqd va foyda"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.get_transaction_type_display()} - {self.amount}"
