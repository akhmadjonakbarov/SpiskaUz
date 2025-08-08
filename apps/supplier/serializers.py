from rest_framework import serializers
from .models import Supplier, DebtPaymentHistory


class SupplierSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)  # Force inclusion of ID

    class Meta:
        model = Supplier
        exclude = ('deleted_at',)


class CreateSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('name', 'phone_number')


class PayDebtSerializer(serializers.Serializer):
    currency_type = serializers.CharField()
    amount = serializers.FloatField(default=0.0)


class DebtPaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtPaymentHistory
        # fields = '__all__'
        exclude = ('deleted_at',)
