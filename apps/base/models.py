from django.db import models
from django.utils import timezone


# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    # active = 
    # objects = models.Manager()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def reset(self):
        self.deleted_at = None
        self.save()

    def hard_delete(self):
        self.delete()

    class Meta:
        abstract = True


class BaseModelWithUser(BaseModel):
    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True


class BaseModelWithShop(BaseModel):
    shop = models.ForeignKey("shops.Shop", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True


class BaseModelWithUserAndShop(BaseModelWithUser, BaseModelWithShop):
    class Meta:
        abstract = True


from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator


class PriceAndQtyMixin(models.Model):
    qty = models.DecimalField(
        max_digits=50, decimal_places=5,
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    income_price = models.DecimalField(
        max_digits=50, decimal_places=5,
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    sale_price = models.DecimalField(
        max_digits=50, decimal_places=5,
        validators=[MinValueValidator(Decimal('0.0'))]
    )

    class Meta:
        abstract = True


class PriceAndQtyMixinWithPercentage(PriceAndQtyMixin):
    profit_as_percent = models.DecimalField(
        max_digits=50, decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.0')),
        ],
    )

    class Meta:
        abstract = True


class CurrencyType(models.TextChoices):
    USD = 'usd', 'USD'
    UZS = 'uzs', 'UZS'


class TransactionType(models.TextChoices):
    CASH = 'cash', 'Cash'
    PROFIT = 'profit', 'Profit'
    LOSS = 'loss', 'Loss'
    CASH_PROFIT = 'cash_profit', 'Cash_Profit'
    CASH_LOSS = 'cash_loss', 'Cash_Loss'
