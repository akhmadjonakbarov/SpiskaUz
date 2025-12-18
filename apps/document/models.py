from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.base.models import BaseModelWithUserAndShop, BaseModel, PriceAndQtyMixinWithPercentage

from apps.currency_rate.models import CurrencyRate
from apps.orders.models import Order
from apps.products.models import Product
from apps.promocodes.models import PromoCode
from apps.supplier.models import Supplier
from constants.currency_choices import CURRENCY_CHOICES


class BaseDocumentItem(BaseModelWithUserAndShop, PriceAndQtyMixinWithPercentage):
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, verbose_name="Product"
    )
    currency_rate = models.ForeignKey(
        CurrencyRate, on_delete=models.CASCADE, null=True, blank=True,
    )
    currency_rate_value = models.DecimalField(
        max_digits=15, decimal_places=3, default=Decimal('0.0')
    )

    class Meta:
        abstract = True


class Document(BaseModelWithUserAndShop):
    DOC_TYPE = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )
    doc_type = models.CharField(max_length=10, choices=DOC_TYPE)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL,
        related_name="documents", blank=True, null=True
    )

    def get_total_outcome_price_uzs(self):

        if hasattr(self, "payment_detail"):
            discount_price = self.payment_detail.total_discount
            if discount_price and discount_price > 0:
                return discount_price

        total = Decimal("0.0")

        for item in self.document_items.all():
            line_total = item.sale_price * item.qty

            # convert to UZS if needed
            if item.product.currency_type != "UZS":
                line_total *= item.currency_rate_value

            total += line_total

        return total


class PaymentDetail(BaseModel):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Card'),
    )

    document = models.OneToOneField(
        Document, on_delete=models.CASCADE, related_name='payment_detail',
    )
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))
    payment_method = models.CharField(choices=PAYMENT_METHODS, max_length=20)
    note = models.TextField(blank=True, null=True)
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.CASCADE, related_name='payment_details', blank=True,
        null=True,
    )
    promo_code_value = models.DecimalField(max_digits=15, decimal_places=5, default=Decimal('0.0'))

    @property
    def shop(self):
        return self.document.shop

    @property
    def user(self):
        return self.document.user

    @property
    def total_discount(self):
        return self.discount + self.promo_code_value


class DocumentItem(BaseDocumentItem):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="document_items"
    )

    def __str__(self):
        return f"{self.product} - {self.qty} - {self.income_price} - {self.document.doc_type}"


class DocumentItemBalance(BaseDocumentItem):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="document_items_balance"
    )
    document_item = models.OneToOneField(
        DocumentItem, on_delete=models.CASCADE, related_name="balance",
    )

    def __str__(self):
        return f"{self.product} - {self.qty} - {self.income_price} - {self.document.doc_type}"


class PaymentInfo(BaseModelWithUserAndShop):
    document = models.OneToOneField(
        Document,
        related_name="payment_info",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    note = models.TextField(blank=True, null=True)

    payed_money = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=Decimal('0.00000'),
        validators=[MinValueValidator(Decimal('0.0'))]
    )

    un_payed_money = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=Decimal('0.00000'),
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    currency_type = models.CharField(max_length=10, choices=CURRENCY_CHOICES)

    def __str__(self):
        return f"{self.document} - {self.note or 'No note'}"


class DocumentOrder(BaseModel):
    document = models.OneToOneField(
        Document, on_delete=models.CASCADE
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE
    )
