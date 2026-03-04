from rest_framework import serializers
from .models import Season, SeasonItem

from django.db import transaction
from rest_framework import serializers
from .models import Season, SeasonItem


class SeasonItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonItem
        fields = ['id', 'price']


class SeasonSerializer(serializers.ModelSerializer):
    items = SeasonItemSerializer(many=True, required=False)

    class Meta:
        model = Season
        fields = ['id', 'name', 'shop', 'user', 'items']
        read_only_fields = ['user']

    @transaction.atomic
    def create(self, validated_data):
        # 1. Extract the nested items data
        items_data = validated_data.pop('items', [])

        # 2. Create the parent Season instance
        # Note: 'user' is passed from the ViewSet's perform_create
        season = Season.objects.create(**validated_data)

        # 3. Create the nested SeasonItems
        for item_data in items_data:
            SeasonItem.objects.create(season=season, **item_data)

        return season

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update Season fields
        instance.name = validated_data.get('name', instance.name)
        instance.shop = validated_data.get('shop', instance.shop)
        instance.save()

        # Handle nested items update (Replace strategy)
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                SeasonItem.objects.create(season=instance, **item_data)

        return instance


class ApplyPrizeSerializer(serializers.Serializer):
    season_item_id = serializers.PrimaryKeyRelatedField(
        queryset=SeasonItem.objects.all()
    )


from rest_framework import serializers
from .models import GameUserBalance, SeasonItem

from rest_framework import serializers
from .models import GameUserBalance, GameItem


class GameUserBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameUserBalance
        fields = ['id', 'user', 'balance']
        read_only_fields = ['balance']


class GameItemSerializer(serializers.ModelSerializer):
    # Pulling details for the frontend to show what was won
    price = serializers.DecimalField(source='season_item.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = GameItem
        fields = ['id', 'season_item', 'price', 'created_at']