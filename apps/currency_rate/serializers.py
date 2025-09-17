from rest_framework import serializers
from .models import CurrencyRate


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ("shop", "rate", 'id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['rate'] = float(instance.rate)
        return data
