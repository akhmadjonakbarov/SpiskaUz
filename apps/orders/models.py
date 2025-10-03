from decimal import Decimal

from django.db import models
from apps.base.models import BaseModel


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    CANCELLED_BY_ADMIN = "cancelled_by_admin", "Cancelled by Admin"


class OrderPaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"


class Order(BaseModel):
    # customer = models.ForeignKey("users.User", on_delete=models.SET_NULL, related_name="customer_orders",
    #                              verbose_name="Customer", null=True, blank=True)
    # shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="orders", verbose_name="Shop")
    # admin = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True,
    #                           related_name="managed_orders", verbose_name="Admin")
    # discount = models.DecimalField("Discount", max_digits=14, decimal_places=2, default=0)
    # paid_amount = models.DecimalField("Paid Amount", max_digits=14, decimal_places=2, default=0)
    # debt = models.DecimalField("Debt", max_digits=14, decimal_places=2, default=0)
    # profit = models.DecimalField("Profit", max_digits=28, decimal_places=2, default=0)
    # comment = models.TextField("Comment", blank=True, null=True)
    # status = models.CharField("Status", max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    customer = models.ForeignKey("users.User", on_delete=models.SET_NULL, related_name="customer_orders",
                                 verbose_name="Customer", null=True, blank=True)
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="orders", verbose_name="Shop")
    admin = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="managed_orders", verbose_name="Admin")
    discount = models.DecimalField("Discount", max_digits=14, decimal_places=2, default=0)
    comment = models.TextField("Comment", blank=True, null=True)
    status = models.CharField("Status", max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    def __str__(self):
        return f"Order #{self.id} - {self.customer} - {self.status}"


class OrderPaymentDetail(BaseModel):

    order = models.OneToOneField(Order, verbose_name="Order", on_delete=models.CASCADE, related_name="payment_detail")
    payed = models.DecimalField(max_digits=60, decimal_places=5, default=Decimal('0.0'))
    un_payed = models.DecimalField(max_digits=60, decimal_places=5, default=Decimal('0.0'))
    payment_method = models.CharField(
        "Payment Method", max_length=20, choices=OrderPaymentMethod.choices,
        default=OrderPaymentMethod.CASH
    )


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Order"
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="order_items",
        verbose_name="Product"
    )
    amount = models.DecimalField(
        verbose_name="Amount", max_digits=50, decimal_places=3
    )

    def __str__(self):
        return f"OrderItem(order={self.order}, product={self.product}, amount={self.amount})"
