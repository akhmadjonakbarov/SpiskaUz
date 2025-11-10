from rest_framework import viewsets
from apps.role_manager.models import Role
from apps.role_manager.serializer import RoleSerializer


class ShopAdminViewset(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
