from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from common.utils import assign_perms

from .models import Admin, Shop, ShopBalance


# @receiver(post_save, sender=Shop)
# def set_shop_permissions(sender, instance, created, **kwargs):
#     if created:
#         product_perms = ["add_product", "delete_product", "change_product"]
#         category_perms = ["add_category", "change_category", "delete_category"]
#         shop_perms = ["change_shop", "delete_shop"]
#         order_perms = ["confirm_order", "cancel_order"]
#
#         assign_perms(product_perms + category_perms + shop_perms + order_perms, instance.owner, instance)
#
#         instance.members.add(instance.owner)
#
#
# @receiver(post_save, sender=Admin)
# def set_chief_admin(sender, instance: Admin, created, **kwargs):
#     if created and instance.type == "chief admin":
#         category_perms = ["add_category", "change_category", "delete_category"]
#         order_perms = ["confirm_order", "cancel_order"]
#         assign_perms(category_perms + order_perms, instance.user, instance.shop)
#

