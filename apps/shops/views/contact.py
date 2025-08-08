from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

from apps.shops.models import ShopContact
from apps.shops.permissions import CanAddShopContact, CanDeleteShopContact
from apps.shops.serializers import SetTelegramLinkSerializer, ShopContactSerializer


class ShopContactViewSet(ModelViewSet):
    serializer_class = ShopContactSerializer
    permission_classes = [IsAuthenticated, CanAddShopContact, CanDeleteShopContact]
    queryset = ShopContact.objects.all()

    @swagger_auto_schema(request_body=SetTelegramLinkSerializer)
    @action(methods=["POST"], detail=False, url_path="set-telegram", serializer_class=SetTelegramLinkSerializer)
    def set_telegram(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shop = serializer.validated_data["shop"]
        link = serializer.validated_data["link"]

        shop.telegram_link = link
        shop.save()

        return Response({"message": "Link muvaffaqqiyatli o'rnatildi"})
