from apps.shops.models import Shop
from apps.users.models import User
from common.permissions import BaseAddObjectPermission


class CanAddTransaction(BaseAddObjectPermission):
    object_model = Shop
    object_id_field = "shop"

    def check_add_permission(self, user: User, shop: Shop):
        is_site_admin = user.is_staff or user.is_superuser

        is_admin = shop.admins.filter(user=user).exists()

        return is_site_admin or is_admin or shop.owner == user
