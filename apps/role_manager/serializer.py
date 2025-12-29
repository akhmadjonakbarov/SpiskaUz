from decimal import Decimal

from rest_framework import serializers

from .models import Role
from ..shops.serializers import ShopSerializerForRole
from ..users.serializers import SimpleUserSerializer


class RoleSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer()
    shop = ShopSerializerForRole()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Role
        exclude = ('deleted_at',)

    # def __init__(self, *args, **kwargs):
    #     exclude_fields = kwargs.pop('exclude_fields', [])
    #     super().__init__(*args, **kwargs)
    #
    #     for field in exclude_fields:
    #         self.fields.pop(field, None)

    def get_balance(self, role):
        from apps.admin_panel.models import SalaryBalance

        balance = SalaryBalance.objects.filter(role=role).first()
        if balance:
            return {
                "balance": balance.balance,
                "personal_salary": balance.personal_salary,
                "global_salary": balance.global_salary,
            }
        return {
            "balance": 0.0,
            "personal_salary": 0.0,
            "global_salary": 0.0,
        }


class CreateOrUpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            'role', 'user', 'shop', 'salary',
            'total_commission_percent',
            'admin_commission_percent'

        )
