from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Season, SeasonItem, GameUserBalance, GameItem
from .serializers import SeasonSerializer, ApplyPrizeSerializer, GameUserBalanceSerializer


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

    def get_queryset(self):
        qr = self.queryset.order_by('-created_at')
        # Filter by shop if provided in query params, otherwise return all
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            return qr.filter(shop_id=shop_id)
        return qr

    def perform_create(self, serializer):
        # Just pass the user; the Serializer's .create() handles the rest
        serializer.save(user=self.request.user)

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
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def perform_update(self, serializer):
        # Update parent
        season = serializer.save()
        items_data = self.request.data.get('items', [])

        if items_data:
            # Smart Update: Remove old items and replace with new ones
            # Or you can implement logic to update specific IDs if needed
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

            GameItem.objects.create(season_item=season_item, game_balance=user_balance)

            # 3. Update balance with the SeasonItem price
            user_balance.balance += season_item.price
            user_balance.save()

        # 4. Return the updated balance data
        return Response(
            GameUserBalanceSerializer(user_balance).data,
            status=status.HTTP_200_OK
        )
