from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Promocode, PromocodeItem
from .serializers import PromocodeItemSerializer, PromocodeSerializer, CreatePromoCodeSerializer


class PromocodeViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Promocode.objects.all()
    serializer_class = PromocodeSerializer

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePromoCodeSerializer
        else:
            return PromocodeSerializer

    def get_queryset(self):
        return Promocode.objects.filter(
            deleted_at=None
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("shop", openapi.IN_QUERY, description="Shop name", type=openapi.TYPE_STRING,
                              required=True),
            openapi.Parameter("code", openapi.IN_QUERY, description="Promocode code", type=openapi.TYPE_STRING,
                              required=True),
        ]
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        shop = request.query_params.get("shop")
        code = request.query_params.get("code")

        if not shop or not code:
            return Response({"detail": "shop and code are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            promocode = self.get_queryset().get(shop=shop, code=code)
        except Promocode.DoesNotExist:
            return Response({"detail": "Promocode topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if not promocode.can_use_promocode(request.user):
            return Response({"detail": "Siz ushbu promokodni allaqachon ishlatgansiz."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(promocode)

        return Response(serializer.data)


class PromocodeItemViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = PromocodeItem.objects.all()
    serializer_class = PromocodeItemSerializer
    permission_classes = [IsAuthenticated]
