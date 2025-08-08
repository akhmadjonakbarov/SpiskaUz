from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated


class BaseAddObjectPermission(BasePermission):
    object_model = None
    object_id_field = ""
    required_permission = ""

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        obj_id = request.data.get(self.object_id_field)

        if obj_id is None:
            raise PermissionDenied(f"{self.object_id_field} is required")

        try:
            obj_instance = self.object_model.objects.get(pk=obj_id)

            return self.check_add_permission(request.user, obj_instance)

        except (self.object_model.DoesNotExist, ValueError, TypeError, AttributeError):
            return False

        except Exception as e:
            raise ValidationError({"error": str(e)}) from e

    def check_add_permission(self, user, obj):
        return user.has_perm(self.required_permission, obj)


class BaseEditDeleteObjectPermission(IsAuthenticated):
    model_name = ""

    def get_permissions(self):
        return {f"change_{self.model_name}": ["PATCH", "PUT"], f"delete_{self.model_name}": ["DELETE"]}

    def has_object_permission(self, request, view, obj):
        permissions = self.get_permissions()

        for perm, methods in permissions.items():
            if request.method in methods:
                return self.check_edit_delete_permission(request.user, perm, obj)

        return request.method in SAFE_METHODS

    def check_edit_delete_permission(self, user, perm, obj):
        return user.has_perm(perm, obj)


class BaseHasPermission(IsAuthenticated):
    required_permission = ""

    def has_object_permission(self, request, view, obj):
        return self.check_permission(request.user, self.required_permission, obj)

    def check_permission(self, user, perm, obj):
        return user.has_perm(perm, obj)
