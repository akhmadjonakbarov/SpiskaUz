from rest_framework import viewsets

from apps.shops.models import Admin
from apps.shops.permissions import CanAddShopAdmin
from apps.shops.serializers import AdminSerializer


class ShopAdminViewset(viewsets.ModelViewSet):
    serializer_class = AdminSerializer
    queryset = Admin.objects.all()
    permission_classes = [CanAddShopAdmin]
