from django.db import transaction
from rest_framework import serializers

from .models import GameUserBalance, GameItem
from .models import Season
from .models import SeasonItem
from ..shops.models import Shop


class ApplyPrizeSerializer(serializers.Serializer):
    season_item_id = serializers.PrimaryKeyRelatedField(
        queryset=SeasonItem.objects.all()
    )


class GameUserBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameUserBalance
        fields = ['id', 'user', 'balance']
        read_only_fields = ['balance']


class GameItemSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField(source='season_item.price', read_only=True)

    class Meta:
        model = GameItem
        fields = ['id', 'season_item', 'price', 'created_at']


class SeasonItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonItem
        fields = ['id', 'price', 'created_at']


class SeasonSerializer(serializers.ModelSerializer):
    items = SeasonItemSerializer(many=True, required=False)

    class Meta:
        model = Season
        fields = ['id', 'end_date', 'has_debt', 'limit_price', 'name', 'shop', 'user', 'items', 'created_at']
        read_only_fields = ['user']


class SeasonCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    limit_price = serializers.IntegerField(write_only=True)
    end_date = serializers.DateTimeField(write_only=True)  # Changed to DateTime to match model
    has_debt = serializers.BooleanField(default=False)

    items = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        default=[],
        write_only=True  # This prevents the KeyError on response
    )
