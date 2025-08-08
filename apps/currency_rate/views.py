from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CurrencyRate
from .serializers import CurrencyRateSerializer


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
        shop_id = request.data.get("shop")
        if not shop_id:
            return Response({"detail": "Shop is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not self.request.user.shops.filter(id=shop_id).exists():
            return Response({"detail": "You don't have access to this shop."}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
