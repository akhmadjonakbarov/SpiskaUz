from rest_framework import permissions

from apps.shops.models import Shop


class IsShopOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method != "POST":
            return True

        shop_id = request.data.get("shop")
        if not shop_id:
            return False

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return False

        user = request.user
        return shop.owner == user or user in shop.admins.all()
