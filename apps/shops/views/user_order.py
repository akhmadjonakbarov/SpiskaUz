from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.permissions import CanViewOrder
from apps.orders.serializers import OrderSerializer
from apps.shops.models import Shop


class ShopUserOrderListView(GenericAPIView):
    queryset = Shop.objects.all()
    permission_classes = [IsAuthenticated, CanViewOrder]
    serializer_class = OrderSerializer

    def get(self, request, customer_id, *args, **kwargs):
        shop = self.get_object()

        orders = Order.objects.filter(shop=shop, customer_id=customer_id)

        serializer = OrderSerializer(orders, many=True, context={"request": request})

        return Response(serializer.data)
