from rest_framework import serializers
from .models import DebtConversion, DebtPayment, Debt


class DebtPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtPayment
        fields = ["id", "shop", "user", "amount", "currency", "paid_at"]
        read_only_fields = ["paid_at"]


class DebtConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtConversion
        fields = ["id", "shop", "user", "amount_uzs", "amount_usd", "converted_at", "reverted"]
        read_only_fields = ["amount_usd", "converted_at", "reverted"]


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = '__all__'
