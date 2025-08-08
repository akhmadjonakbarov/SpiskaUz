from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import Notification, NotificationType

from .models import Product


@receiver(post_save, sender=Product)
def create_product_notification(sender, instance: Product, created, **kwargs):
    if created:
        shop = instance.shop
        notifications = [
            Notification(
                shop=shop,
                user=member,
                type=NotificationType.NEW_PRODUCT,
                product=instance,
            )
            for member in shop.members.all()
        ]

        Notification.objects.bulk_create(notifications)
