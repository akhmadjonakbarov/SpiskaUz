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

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', [])
        super().__init__(*args, **kwargs)

        for field in exclude_fields:
            self.fields.pop(field, None)


class CreateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            'role', 'user', 'shop', 'salary',
            'total_commission_percent',
            'admin_commission_percent'

        )
