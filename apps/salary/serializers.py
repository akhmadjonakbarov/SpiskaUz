from rest_framework import serializers
from apps.role_manager.models import Role
from apps.salary.models import SalaryTransaction


class CreateSalaryTransaction(serializers.Serializer):
    user_role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    amount = serializers.DecimalField(max_digits=50, decimal_places=5)
    description = serializers.CharField(max_length=500)

    def create(self, validated_data):
        request = self.context.get("request")
        role = validated_data.get("user_role")
        user = validated_data.get("created_by")
        amount = validated_data.get("amount")
        desc = validated_data.get("description")

        # Example: override created_by with request.user
        if request:
            user = request.user

        transaction = SalaryTransaction.objects.create(
            user_role=role,
            created_by=user,
            amount=amount,
            description=desc
        )

        return transaction


class SalaryTransactionSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = SalaryTransaction
        fields = "__all__"

    def get_user_role(self, obj: SalaryTransaction):
        from apps.role_manager.serializer import RoleSerializer
        return RoleSerializer(obj.user_role, many=False, read_only=True).data

    def get_created_by(self, obj: SalaryTransaction):
        from apps.users.serializers import SimpleUserSerializer
        return SimpleUserSerializer(obj.created_by, many=False, read_only=True).data
