from django.contrib.auth import get_user_model
from django.db import models

from apps.orders.models import Order
from apps.products.models import Product
from apps.shops.models import Shop

User = get_user_model()


class NotificationType(models.TextChoices):
    NEW_PRODUCT = ("new_product", "New product")
    ORDER_EVENT_USER = ("order_event_user", "Order event from user")
    ORDER_EVENT_ADMIN = ("order_event_admin", "Order event from admin")


class Notification(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="notifications")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(choices=NotificationType.choices, max_length=128)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, default=None)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
