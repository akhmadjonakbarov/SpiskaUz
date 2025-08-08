from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import Notification, NotificationType

from .models import Order


@receiver(post_save, sender=Order)
def create_order_notification(sender, instance: Order, created, **kwargs):
    if created:
        Notification.objects.create(
            shop=instance.shop,
            user=instance.customer,
            order=instance,
            type=NotificationType.ORDER_EVENT_ADMIN,
        )
