from rest_framework import permissions, viewsets

from .models import DebtConversion, DebtPayment
from .serializers import DebtConversionSerializer, DebtPaymentSerializer


class DebtConversionViewSet(viewsets.ModelViewSet):
    serializer_class = DebtConversionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DebtConversion.objects.all()


class DebtPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = DebtPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DebtPayment.objects.all()
