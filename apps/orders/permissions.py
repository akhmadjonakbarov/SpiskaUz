from apps.role_manager.models import Role
from common.permissions import BaseHasPermission


class CanCancelOrder(BaseHasPermission):
    required_permission = "cancel_order"

    def check_permission(self, user, perm, obj):
        """
        Do'kon admini bo'lishi kerak yoki faqat o'z orderini bekor qilishga ruxsat beriladi
        """
        return obj.customer == user or super().check_permission(user, perm, obj.shop)


class CanRestoreOrder(BaseHasPermission):
    def check_permission(self, user, perm, obj):
        """
        Faqat o'z orderini savatga ko'chirishga ruxsat beriladi
        """
        return obj.customer == user or user.is_superuser or user.is_staff


class CanDeleteOrder(BaseHasPermission):
    def has_object_permission(self, request, view, obj):
        """
        Faqat o'z orderini o'chirishga ruxsat berish
        """

        if request.method == "DELETE":
            user = request.user

            return obj.customer == user or user.is_superuser or user.is_staff

        return True


class CanViewOrder(BaseHasPermission):
    def has_object_permission(self, request, view, obj):
        role = Role.objects.filter(
            user=request.user, shop=obj
        ).first()
        if role:
            return True
        else:
            return request.user.is_staff or request.user.is_superuser  # ! Permission ga tekshirishni qo'shish kerak
