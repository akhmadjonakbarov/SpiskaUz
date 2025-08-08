from django.db import models

from apps.base.models import BaseModelWithUserAndShop


# Create your models here.
class CurrencyRate(BaseModelWithUserAndShop):
    rate = models.DecimalField(
        max_digits=50, decimal_places=5,
    )

    def __str__(self):
        return str(self.rate)
