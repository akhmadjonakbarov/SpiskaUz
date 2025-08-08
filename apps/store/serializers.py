from rest_framework import serializers

from apps.currency_rate.serializers import CurrencyRateSerializer
from apps.document.models import DocumentItemBalance
from apps.products.serializers import ProductSerializer


class StoreSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False)
    currency_rate = CurrencyRateSerializer(many=False)

    class Meta:
        model = DocumentItemBalance

        exclude = ["deleted_at", 'updated_at', 'document', 'document_item']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        decimal_fields = [
            "qty",
            "income_price",
            "sale_price",
            "profit_as_percent",
            "currency_rate_value",
        ]

        for field in decimal_fields:
            value = data.get(field)
            if value is not None:
                try:
                    data[field] = float(value)
                except (ValueError, TypeError):
                    pass  # skip if conversion fails

        return data

