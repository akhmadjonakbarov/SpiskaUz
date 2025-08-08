from django.db.models.signals import post_save
from django.dispatch import receiver

from common.utils import assign_perms

from .models import Advertisement


@receiver(post_save, sender=Advertisement)
def set_advertisement_permissions(sender, instance, created, **kwargs):
    if created:
        assign_perms(["change_advertisement", "delete_advertisement"], instance.owner, instance)
