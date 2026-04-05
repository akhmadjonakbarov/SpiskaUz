from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import GameUserBalance, GameItem
from .models import Season
from .models import SeasonItem
from ..shops.models import Shop


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

    class Meta:
        model = SeasonItem
        fields = ["id", "price", "user_opportunity", "ticket_count"]

    def get_user_opportunity(self, obj):
        request = self.context.get("request")
        shop_id = request.query_params.get("shop")

        # Calculate 10% limit
        total_spent = request.user.customer_orders.filter(shop_id=shop_id).aggregate(
            total=Sum("payment_detail__payed"))["total"] or Decimal("0.0")

        # Returns 1 if under cap, 0 if over
        return 1 if obj.price <= (float(total_spent) * 0.10) else 0

    def get_ticket_count(self, obj):
        # Your specific "Opportunity" rules
        price = obj.price
        if price <= 20:
            return 5  # $10 and $20 get 5 tickets
        if price <= 40:
            return 3  # $30 and $40 get 3 tickets
        if price <= 70:
            return 2  # $50, $60, $70 get 2 tickets
        return 1  # $80, $90, $100 get 1 ticket


class SeasonSerializer(serializers.ModelSerializer):
    items = SeasonItemSerializer(many=True, required=False)
    is_game_played = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ["id", "end_date", "limit_price",
                  "name", "shop", "user", "items", "created_at", "is_game_played"]
        read_only_fields = ["user"]

    def get_is_game_played(self, season: Season):
        user = self.context.get("request").user
        return user in season.played_users.all()


class SeasonCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    limit_price = serializers.IntegerField(write_only=True)
    # Changed to DateTime to match model
    end_date = serializers.DateTimeField(write_only=True)
    has_debt = serializers.BooleanField(default=False)

    items = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        default=[],
        write_only=True,  # This prevents the KeyError on response
    )
