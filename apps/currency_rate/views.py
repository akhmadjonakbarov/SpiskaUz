from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.document.models import DocumentItemBalance
from apps.product_part.models import ProductPart
from .models import CurrencyRate
from .serializers import CurrencyRateSerializer
from ..role_manager.models import Role
from ..shops.models import Shop


class LatestCurrencyRate(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(shop__in=self.request.user.shops.all())
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset.order_by('-created_at').first()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shop_id', openapi.IN_QUERY, description="Filter by shop ID",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def retrieve(self, request, pk=None):
        rate = self.get_queryset()
        serializer = self.serializer_class(rate, many=False)
        return Response(serializer.data)


class CurrencyRateListView(viewsets.ViewSet):
    serializer_class = CurrencyRateSerializer
    permission_classes = [IsAuthenticated]
    queryset = CurrencyRate.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(shop__in=self.request.user.shops.all())
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset.order_by('-created_at')

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shop_id', openapi.IN_QUERY, description="Filter by shop ID",
                type=openapi.TYPE_STRING
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class CurrencyRateCreateView(generics.CreateAPIView):
    serializer_class = CurrencyRateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        shop_id = request.data.get("shop", None)
        rate = request.data.get("rate", None)
        if not shop_id:
            return Response({"detail": "Shop is required."}, status=status.HTTP_400_BAD_REQUEST)

        role = Role.objects.filter(deleted_at=None, user=request.user, shop_id=shop_id).first()

        if role is None or role.role != 'owner':
            return Response({"detail": "You don't have access to this shop."}, status=status.HTTP_403_FORBIDDEN)

        try:
            shop = Shop.objects.get(id=shop_id)
            currency_rate = CurrencyRate.objects.create(
                shop=shop, user=request.user, rate=rate
            )

            product_parts = ProductPart.objects.filter(
                shop=shop_id, is_confirm=False
            )
            balances = (
                DocumentItemBalance.objects
                .filter(shop=shop)
                .select_related("document_item")  # OneToOne => select_related
            )

            if balances:
                for balance in balances:
                    # Update balance
                    balance.currency_rate = currency_rate
                    balance.currency_rate_value = currency_rate.rate

                    balance.save(update_fields=["currency_rate", "currency_rate_value"])

            if product_parts:
                for pp in product_parts:
                    pp.currency_rate = currency_rate
                    pp.currency_rate_value = currency_rate.rate
                    pp.save()

            serializer = self.get_serializer(currency_rate, many=False)
            return Response(
                data=serializer.data
            )
        except Exception as e:
            print(e)
            return Response(
                data={
                    'error': e
                }
            )


# Retrieve View
class CurrencyRateRetrieveView(generics.RetrieveAPIView):
    serializer_class = CurrencyRateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CurrencyRate.objects.filter(shop__in=self.request.user.shops.all())


# Update View
class CurrencyRateUpdateView(generics.UpdateAPIView):
    serializer_class = CurrencyRateSerializer
    permission_classes = (IsAuthenticated,)
    queryset = CurrencyRate.objects.all()

    class CurrencyRateUpdateView(generics.UpdateAPIView):
        serializer_class = CurrencyRateSerializer
        permission_classes = (IsAuthenticated,)

        def get_queryset(self):
            if self.request.user.is_authenticated:
                return CurrencyRate.objects.filter(
                    shop__in=self.request.user.shops.all()
                )
            else:
                # You can raise a permission denied exception here if needed
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have permission to access this resource.")


# Delete View
class CurrencyRateDeleteView(generics.DestroyAPIView):
    serializer_class = CurrencyRateSerializer
    permission_classes = [IsAuthenticated, ]
    queryset = CurrencyRate.objects.all()

    def destroy(self, request, *args, **kwargs):
        currency: CurrencyRate = self.get_object()
        currency.soft_delete()
        return Response(
            data={
                'detail': 'Currency was deleted'
            }
        )
