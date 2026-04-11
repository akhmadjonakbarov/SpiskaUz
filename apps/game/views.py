from decimal import Decimal
import random
from decimal import Decimal
from django.db import transaction
from rest_framework.response import Response
from django.db.models import Sum

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from django.db import transaction
from .models import Season, SeasonItem, GameUserBalance, GameItem

from .serializers import SeasonSerializer, SeasonCreateSerializer, get_ticket_count
from apps.orders.models import OrderPaymentDetail
from apps.role_manager.models import Role


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qr = self.queryset.order_by("-created_at")

        shop_id = self.request.query_params.get("shop")
        if shop_id:
            return qr.filter(shop_id=shop_id)
        return qr

    def get_serializer_class(self):
        # Use the specific creation serializer for POST requests
        if self.action == "create":
            return SeasonCreateSerializer
        return SeasonSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        # Extract data
        items_list = serializer.validated_data.pop("items", [])

        # Create Season (validated_data now contains name, shop, limit_price, end_date)
        season = Season.objects.create(
            user=self.request.user, **serializer.validated_data)

        # Create Items
        SeasonItem.objects.bulk_create(
            [SeasonItem(season=season, price=p) for p in items_list])

        # Assign the instance back so the ViewSet can find it
        serializer.instance = season

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        # FIX: Pass the context here!
        output_serializer = SeasonSerializer(
            serializer.instance,
            context={'request': request}
        )

        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(manual_parameters=[openapi.Parameter("shop", openapi.IN_QUERY, description="Filter seasons by Shop ID", type=openapi.TYPE_INTEGER)], responses={200: SeasonSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        user = request.user

        if user.is_staff or user.is_superuser:
            return Response([])

        shop_id = request.query_params.get("shop")
        has_no_debt = False

        role = Role.objects.filter(user=user, shop=shop_id).first()

        if role is not None:
            return super().list(request, *args, **kwargs)

        orders = user.customer_orders.filter(shop_id=shop_id)
        total = Decimal("0.0")
        latest_season: Season = Season.objects.order_by(
            "-created_at").filter(shop_id=shop_id).first()
        if latest_season is None:
            return Response([])

        has_played = GameItem.objects.filter(
            season=latest_season, game_balance__user=user).exists()

        if has_played:
            return Response(data={"message": "User already played this game"}, status=403)

        for order in orders:
            payment_detail: OrderPaymentDetail = order.payment_detail
            total += payment_detail.payed

        high_spender = total >= latest_season.limit_price
        if not high_spender:
            return Response([])
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def perform_update(self, serializer):
        # Update parent
        season = serializer.save()
        items_data = self.request.data.get("items", [])

        if items_data:
            season.items.all().delete()
            for item in items_data:
                SeasonItem.objects.create(season=season, **item)

    @action(detail=False, methods=["get"], url_path="last-game/(?P<shop_id>[^/.]+)")
    @transaction.atomic
    def get_last_game(self, request, shop_id: int):
        """
        Returns the last season for the shop.
        - If user hasn't played yet: runs the prize selection, records the result, returns season with won item marked.
        - If user already played: returns season with their previously won item marked.
        """
        user = request.user

        last_season = Season.actives.filter(
            shop_id=shop_id).order_by('-created_at').first()
        if not last_season:
            return Response({"detail": "No active season found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if user already played
        existing_game_item = GameItem.objects.filter(
            season_item__season=last_season,
            game_balance__user=user
        ).select_related("season_item").first()

        if existing_game_item:
            # Already played — just return with the previously won item marked
            won_item_id = existing_game_item.season_item.id
        else:
            # First visit — run prize selection
            total_spent = user.customer_orders.filter(shop_id=shop_id).aggregate(
                total=Sum("payment_detail__payed")
            )["total"] or Decimal("0.0")

            max_prize = float(total_spent) * 0.10

            eligible_items = [
                item for item in last_season.items.all() if item.price <= max_prize]
            if not eligible_items:
                return Response({"detail": "You are not eligible for any prize."}, status=status.HTTP_400_BAD_REQUEST)

            # Build weighted pool and pick winner
            weighted_pool = []
            for item in eligible_items:
                weighted_pool.extend([item] * get_ticket_count(item.price))
            won_item = random.choice(weighted_pool)

            # Record result
            user_balance, _ = GameUserBalance.objects.select_for_update().get_or_create(
                user=user, defaults={"balance": Decimal("0.0")}
            )
            GameItem.objects.create(
                season_item=won_item,
                game_balance=user_balance,
                season=last_season
            )
            user_balance.balance += won_item.price
            user_balance.save()
            last_season.played_users.add(user)

            won_item_id = won_item.id

        serializer = SeasonSerializer(
            last_season,
            context={"request": request, "shop_id": shop_id,
                     "won_item_id": won_item_id}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
