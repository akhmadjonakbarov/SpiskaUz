from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.debt.models import DebtConversion
from apps.debt.serializers import DebtConversionSerializer
from apps.orders.permissions import CanViewOrder
from apps.shops.models import Shop


class ShopUserConversionListView(GenericAPIView):
    queryset = Shop.objects.all()
    permission_classes = [IsAuthenticated, CanViewOrder]
    serializer_class = DebtConversionSerializer

    def get(self, request, customer_id, *args, **kwargs):
        shop = self.get_object()

        conversions = DebtConversion.objects.filter(shop=shop, user_id=customer_id)

        serializer = DebtConversionSerializer(conversions, many=True, context={"request": request})

        return Response(serializer.data)
