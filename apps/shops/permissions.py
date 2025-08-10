from apps.shops.models import Shop
from apps.users.models import User
from common.permissions import BaseAddObjectPermission, BaseEditDeleteObjectPermission
from rest_framework.permissions import BasePermission


class CanEditDeleteShop(BaseEditDeleteObjectPermission):
    model_name = "shop"


class CanAddShopCategory(BaseAddObjectPermission):
    object_model = Shop
    object_id_field = "shop"
    required_permission = "add_category"


class CanEditShopCategory(BaseEditDeleteObjectPermission):
    model_name = "category"

    def check_edit_delete_permission(self, user, perm, obj):
        return super().check_edit_delete_permission(user, perm, obj.shop)


class CanAddShopContact(BaseAddObjectPermission):
    object_model = Shop
    object_id_field = "shop"

    def check_add_permission(self, user, obj):
        return obj.owner == user


class CanDeleteShopContact(BaseEditDeleteObjectPermission):
    def has_object_permission(self, request, view, obj):
        return obj.shop.owner == request.user


class CanAddShopAdmin(BaseAddObjectPermission):
    object_model = Shop
    object_id_field = "shop"

    def check_add_permission(self, user: User, obj):
        is_site_admin = user.is_staff or user.is_superuser

        return is_site_admin or obj.owner == user
