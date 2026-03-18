from decimal import Decimal

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Season, SeasonItem, GameUserBalance, GameItem

from .serializers import SeasonSerializer, ApplyPrizeSerializer, GameUserBalanceSerializer, SeasonCreateSerializer
from ..orders.models import OrderPaymentDetail
from ..role_manager.models import Role


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qr = self.queryset.order_by('-created_at')

        shop_id = self.request.query_params.get('shop')
        if shop_id:
            return qr.filter(shop_id=shop_id)
        return qr

    def get_serializer_class(self):
        # Use the specific creation serializer for POST requests
        if self.action == 'create':
            return SeasonCreateSerializer
        return SeasonSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        # Extract data
        items_list = serializer.validated_data.pop('items', [])

        # Create Season (validated_data now contains name, shop, limit_price, end_date)
        season = Season.objects.create(
            user=self.request.user,
            **serializer.validated_data
        )

        # Create Items
        SeasonItem.objects.bulk_create([
            SeasonItem(season=season, price=p)
            for p in items_list
        ])

        # Assign the instance back so the ViewSet can find it
        serializer.instance = season

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        output_serializer = SeasonSerializer(serializer.instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shop',
                openapi.IN_QUERY,
                description="Filter seasons by Shop ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: SeasonSerializer(many=True)}
    )
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
        total = Decimal('0.0')
        latest_season: Season = Season.objects.order_by('-created_at').filter(shop_id=shop_id).first()
        if latest_season is None:
            return Response([])

        has_played = GameItem.objects.filter(
            season=latest_season,
            game_balance__user=user
        ).exists()

        if has_played:
            return Response(data={
                "message": "User already played this game"
            }, status=403)

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
        items_data = self.request.data.get('items', [])

        if items_data:

            season.items.all().delete()
            for item in items_data:
                SeasonItem.objects.create(season=season, **item)

    @swagger_auto_schema(
        operation_description="Apply a prize from a specific SeasonItem to the user's balance.",
        request_body=ApplyPrizeSerializer,
        responses={200: GameUserBalanceSerializer(), 400: "Invalid Item"}
    )
    @action(detail=False, methods=['post'], url_path='apply-prize')
    def apply_prize(self, request):
        serializer = ApplyPrizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        season_item = serializer.validated_data['season_item_id']
        user = request.user

        with transaction.atomic():
            user_balance, created = GameUserBalance.objects.select_for_update().get_or_create(
                user=user,
                defaults={'balance': 0}
            )

            GameItem.objects.create(
                season_item=season_item,
                game_balance=user_balance,
                season=season_item.season
            )

            user_balance.balance += season_item.price
            user_balance.save()

        # 4. Return the updated balance data
        return Response(
            GameUserBalanceSerializer(user_balance).data,
            status=status.HTTP_200_OK
        )
