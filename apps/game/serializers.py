from decimal import Decimal
from django.db.models import Sum
from rest_framework import serializers
from .models import GameUserBalance, GameItem, Season, SeasonItem
from ..shops.models import Shop


def get_ticket_count(price):
    if price <= 20:
        return 5
    if price <= 40:
        return 3
    if price <= 70:
        return 2
    return 1


class PlayGameSerializer(serializers.Serializer):
    shop_id = serializers.IntegerField()


class ApplyPrizeSerializer(serializers.Serializer):
    season_item_id = serializers.PrimaryKeyRelatedField(
        queryset=SeasonItem.objects.all())


class GameUserBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameUserBalance
        fields = ["id", "user", "balance"]
        read_only_fields = ["balance"]


class GameItemSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField(
        source="season_item.price", read_only=True)

    class Meta:
        model = GameItem
        fields = ["id", "season_item", "price", "created_at"]


class SeasonItemSerializer(serializers.ModelSerializer):
    user_opportunity = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    is_won = serializers.SerializerMethodField()

    class Meta:
        model = SeasonItem
        fields = ["id", "price", "user_opportunity", "ticket_count", "is_won"]

    def get_user_opportunity(self, obj):
        total_spent = self.context.get("total_spent", 0.0)
        return 1 if obj.price <= total_spent * 0.10 else 0

    def get_ticket_count(self, obj):
        return get_ticket_count(obj.price)

    def get_is_won(self, obj):
        # won_item_id is injected by SeasonSerializer after prize selection
        won_item_id = self.context.get("won_item_id")
        return obj.id == won_item_id


class SeasonSerializer(serializers.ModelSerializer):
    items = SeasonItemSerializer(many=True, required=False)
    is_game_played = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ["id", "end_date", "limit_price",
                  "name", "shop", "user", "items", "created_at", "is_game_played"]
        read_only_fields = ["user"]

    def to_representation(self, instance):
        request = self.context.get("request")
        shop_id = request.query_params.get(
            "shop") or self.context.get("shop_id")

        # Compute total_spent once and pass down to child serializer
        total_spent = request.user.customer_orders.filter(shop_id=shop_id).aggregate(
            total=Sum("payment_detail__payed")
        )["total"] or Decimal("0.0")

        self.context["total_spent"] = float(total_spent)
        return super().to_representation(instance)

    def get_is_game_played(self, season: Season):
        user = self.context.get("request").user
        return GameItem.objects.filter(
            season_item__season=season,
            game_balance__user=user
        ).exists()


class SeasonCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    limit_price = serializers.IntegerField(write_only=True)
    end_date = serializers.DateTimeField(write_only=True)
    has_debt = serializers.BooleanField(default=False)
    items = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        default=[],
        write_only=True,
    )
