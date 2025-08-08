from apps.products.models import Product
from apps.shops.models import Shop
from common.permissions import BaseAddObjectPermission, BaseEditDeleteObjectPermission


class CanAddProduct(BaseAddObjectPermission):
    object_model = Shop
    object_id_field = "shop"
    required_permission = "add_product"


class CanEditDeleteProduct(BaseEditDeleteObjectPermission):
    model_name = "product"

    def check_edit_delete_permission(self, user, perm, obj):
        return super().check_edit_delete_permission(user, perm, obj.shop)


class CanAddProductPart(BaseAddObjectPermission):
    object_model = Product
    object_id_field = "product"
    required_permission = "add_product"

    def check_add_permission(self, user, obj):
        return super().check_add_permission(user, obj.shop)


class CanEditDeleteProductPart(BaseEditDeleteObjectPermission):
    model_name = "product"

    def check_edit_delete_permission(self, user, perm, obj):
        return super().check_edit_delete_permission(user, perm, obj.product.shop)
