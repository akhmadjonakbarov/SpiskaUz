from http.client import HTTPException

from django.http import Http404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.document.models import Document
from apps.shops.models import Shop
from apps.statistics.selectors.document_selector import DocumentSelector, ShopBalanceTransactionSelector
from apps.statistics.services.bought_statistic_service import BoughtStatisticService
from apps.statistics.services.sold_statistic_service import SoldStatisticService


class BaseStatisticView(GenericAPIView):
    serializer_class = None
    queryset = Document.actives.all()
    permission_classes = (IsAuthenticated,)
    doc_type = None

    def get_queryset(self):
        return Document.actives.filter(
            doc_type=self.doc_type, shop_id=self.kwargs['shop_id'],
        ).order_by('-created_at')

    def get_shop(self):
        try:
            return Shop.objects.get(id=self.kwargs['shop_id'])
        except Shop.DoesNotExist:
            raise NotFound(detail="Shop not found", code=status.HTTP_404_NOT_FOUND)


class BoughtStatisticView(BaseStatisticView):
    doc_type = 'buy'

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "from_date", openapi.IN_QUERY, description="From date",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "to_date", openapi.IN_QUERY, description="To date",
                type=openapi.TYPE_STRING
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        shop = self.get_shop()
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        documents = DocumentSelector.filter_documents(
            shop=shop,
            doc_type=self.doc_type,
            from_date=from_date,
            to_date=to_date
        )
        data = BoughtStatisticService(shop, documents, ).calculate(from_date=from_date, to_date=to_date)

        return Response(
            data=data
        )


class SoldStatisticView(BaseStatisticView):
    permission_classes = (IsAuthenticated,)
    doc_type = 'sell'

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "from_date", openapi.IN_QUERY, description="From date",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "to_date", openapi.IN_QUERY, description="To date",
                type=openapi.TYPE_STRING
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        shop = self.get_shop()
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        documents = DocumentSelector.filter_documents(
            shop=shop,
            doc_type=self.doc_type,
            from_date=from_date,
            to_date=to_date
        )

        shop_balance_transactions = ShopBalanceTransactionSelector.filter_shop_balance_transactions(
            shop=shop, from_date=from_date, to_date=to_date
        )
        data = SoldStatisticService(shop, documents, shop_balance_transactions).calculate()

        return Response(
            data=data
        )
