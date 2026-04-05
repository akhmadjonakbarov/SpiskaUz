from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Season, SeasonItem, GameUserBalance, GameItem

from .serializers import SeasonSerializer, ApplyPrizeSerializer, GameUserBalanceSerializer, SeasonCreateSerializer, PlayGameSerializer
from ..orders.models import OrderPaymentDetail
from ..role_manager.models import Role


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
        output_serializer = SeasonSerializer(serializer.instance)
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

    @swagger_auto_schema(operation_description="Apply a prize from a specific SeasonItem to the user's balance.", request_body=ApplyPrizeSerializer, responses={200: GameUserBalanceSerializer(), 400: "Invalid Item"})
    @action(detail=False, methods=["post"], url_path="apply-prize")
    def apply_prize(self, request):
        serializer = ApplyPrizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        season_item = serializer.validated_data["season_item_id"]
        user = request.user

        with transaction.atomic():
            user_balance, created = GameUserBalance.objects.select_for_update(
            ).get_or_create(user=user, defaults={"balance": 0})

            GameItem.objects.create(
                season_item=season_item, game_balance=user_balance, season=season_item.season)

            user_balance.balance += season_item.price
            user_balance.save()

        # 4. Return the updated balance data
        return Response(GameUserBalanceSerializer(user_balance).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_description="Play the game for a specific shop.", request_body=PlayGameSerializer, responses={200: SeasonSerializer()})
    @action(detail=False, methods=["post"], url_path="play")
    def play_game(self, request):
        serializer = PlayGameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shop_id = serializer.validated_data["shop_id"]
        user = request.user

        latest_season = Season.objects.filter(
            shop_id=shop_id).order_by("-created_at").first()
        if latest_season is None:
            return Response({"error": "No active season for this shop"}, status=status.HTTP_404_NOT_FOUND)

        if latest_season.end_date and latest_season.end_date < timezone.now():
            return Response({"error": "Season has ended"}, status=status.HTTP_400_BAD_REQUEST)

        has_played = GameItem.objects.filter(
            season=latest_season, game_balance__user=user).exists()

        if has_played:
            return Response({"message": "User already played this game"}, status=status.HTTP_400_BAD_REQUEST)

        total = user.customer_orders.filter(shop_id=shop_id).aggregate(
            total=Sum("payment_detail__payed"))["total"] or Decimal("0.0")

        if total < latest_season.limit_price:
            return Response({"error": f"Spending below limit. Required: {latest_season.limit_price}, Actual: {total}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SeasonSerializer(latest_season, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="last-game/(?P<shop_id>[^/.]+)")
    def get_last_game(self, request, shop_id: int):
        """
        Returns the last game played by the user.
        """
        try:
            last_game = (
                Season.actives.all().order_by('-created_at').first()
            )
            serializer = SeasonSerializer(
                last_game, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
