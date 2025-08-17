from rest_framework import serializers
from .models import Supplier, DebtPaymentHistory
from apps.shops.models import Shop


class SupplierSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)  # Force inclusion of ID

    class Meta:
        model = Supplier
        exclude = ('deleted_at',)


class CreateSupplierSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.all()
    )

    class Meta:
        model = Supplier
        fields = ('name', 'phone_number', 'shop')


class PayDebtSerializer(serializers.Serializer):
    currency_type = serializers.CharField()
    amount = serializers.FloatField(default=0.0)


class DebtPaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtPaymentHistory
        # fields = '__all__'
        exclude = ('deleted_at',)
