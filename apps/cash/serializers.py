from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import CashHistory, CashHistoryItem


class CashHistoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashHistoryItem
        exclude = ("cash_history",)

    def validate(self, data):
        product = data["product"]
        amount = data["amount"]

        if product.stock < amount:
            raise ValidationError({"error": "The product is not enough."})
        product.decrease_stock(amount)

        return data


class CashHistorySerializer(serializers.ModelSerializer):
    items = CashHistoryItemSerializer(many=True, write_only=True)

    class Meta:
        model = CashHistory
        fields = ["id", "shop", "payment_method", "comment", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        cash_history = CashHistory.objects.create(**validated_data)

        items = [CashHistoryItem(cash_history=cash_history, **item_data) for item_data in items_data]
        CashHistoryItem.objects.bulk_create(items)

        return cash_history

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["items"] = CashHistoryItemSerializer(instance.cash_history_item.all(), many=True).data
        return data
