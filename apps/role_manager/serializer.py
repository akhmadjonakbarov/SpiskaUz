from rest_framework import serializers

from .models import Role
from ..shops.serializers import ShopSerializerForRole
from ..users.serializers import SimpleUserSerializer


class RoleSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer()
    shop = ShopSerializerForRole()

    class Meta:
        model = Role
        exclude = ('deleted_at',)

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', [])
        super().__init__(*args, **kwargs)

        for field in exclude_fields:
            self.fields.pop(field, None)


class CreateOrUpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            'role', 'user', 'shop', 'salary',
            'total_commission_percent',
            'admin_commission_percent'

        )
