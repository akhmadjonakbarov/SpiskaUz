from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.debt.models import DebtPayment
from apps.debt.serializers import DebtPaymentSerializer
from apps.orders.permissions import CanViewOrder
from apps.shops.models import Shop


class ShopUserPaymentsListView(GenericAPIView):
    queryset = Shop.objects.all()
    permission_classes = [IsAuthenticated, CanViewOrder]
    serializer_class = DebtPaymentSerializer

    def get(self, request, customer_id, *args, **kwargs):
        shop = self.get_object()

        payments = DebtPayment.objects.filter(shop=shop, user_id=customer_id)

        serializer = DebtPaymentSerializer(payments, many=True, context={"request": request})

        return Response(serializer.data)
