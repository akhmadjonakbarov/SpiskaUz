from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DebtConversion, DebtPayment, Debt
from .serializers import DebtConversionSerializer, DebtPaymentSerializer, DebtSerializer


class DebtConversionViewSet(viewsets.ModelViewSet):
    serializer_class = DebtConversionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DebtConversion.objects.all()


class DebtPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = DebtPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DebtPayment.objects.all()


class DebtViewSet(viewsets.ModelViewSet):
    serializer_class = DebtSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Debt.objects.all()

    @action(detail=True, methods=['post'], url_path="pay", )
    def pay(self, request, pk=None):
        debt = self.get_object()
        debt.is_paid = True
        debt.save()
        return Response(
            data={'detail': 'Debt was paid'}
        )

    @action(detail=True, methods=['post'], url_path="accept")
    def accept(self, request, pk=None):
        debt = self.get_object()
        debt.accept()
        return Response(
            data={'detail': 'Debt was accepted'}
        )
