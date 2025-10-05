from rest_framework import serializers
from .models import Role
from ..shops.serializers import ShopSerializer, ShopSerializerForRole
from ..users.serializers import UserSerializer


class RoleSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    shop = ShopSerializerForRole()

    class Meta:
        model = Role
        fields = ('role', 'user', 'shop')


class CreateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            'role', 'user', 'shop', 'salary',
            'total_approved_orders_commission_percentage',
            'admin_approved_orders_commission_percentage'
        )
