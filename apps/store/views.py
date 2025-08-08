from decimal import Decimal
from typing import List

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.request import Request
from yaml import DocumentEndEvent

from apps.document.models import DocumentItemBalance
from .serializers import StoreSerializer

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets


class StoreView(GenericAPIView):
    serializer_class = StoreSerializer
    permission_classes = (IsAuthenticated,)
    queryset = DocumentItemBalance.objects.all()

    def get_queryset(self):
        shop_id = self.request.query_params.get("shop_id")  # shop_id from URL query

        queryset = DocumentItemBalance.objects.all()

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)

        return queryset

    def get(self, request):
        queryset = self.get_queryset().filter(
            user=request.user,
        )
        total_profit = self.calculate_profit()
        serializer = self.get_serializer(queryset, many=True)
        return Response(data={
            'total_profit': total_profit,
            'products': serializer.data
        })

    def calculate_profit(self) -> float:
        query = self.get_queryset()
        total_profit = Decimal('0.0')

        for item in query:
            if item.product.currency_type == 'usd':
                profit = (Decimal(item.sale_price) - Decimal(item.income_price)) * Decimal(item.currency_rate_value)
            else:
                profit = Decimal(item.sale_price) - Decimal(item.income_price)

            total_profit += profit * Decimal(item.qty)

        return float(total_profit)


class StoreByShop(viewsets.ViewSet):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "product_id",
                openapi.IN_QUERY,
                description="Filter by product ID",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def retrieve(self, request: Request, shop_id=None):
        product_id = request.query_params.get('product_id')
        queryset = DocumentItemBalance.objects.filter(
            shop_id=shop_id, shop__in=request.user.shops.all()
        )
        total_profit = self.calculate_profit(queryset)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            total_profit = self.calculate_profit(queryset)
        serializer = StoreSerializer(queryset, many=True)
        return Response(data={
            'total_profit': total_profit,
            'products': serializer.data
        })

    def calculate_profit(self, query) -> float:
        total_profit = Decimal('0.0')
        for item in query:
            if item.product.currency_type == 'usd':
                profit = (Decimal(item.sale_price) - Decimal(item.income_price)) * Decimal(item.currency_rate_value)
            else:
                profit = Decimal(item.sale_price) - Decimal(item.income_price)

            total_profit += profit * Decimal(item.qty)

        return float(total_profit)
