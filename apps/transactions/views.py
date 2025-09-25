from rest_framework import viewsets

from .models import Transaction
from .permissions import CanAddTransaction
from ..customer_transaction.models import CustomerTransaction


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerTransaction.objects.all()
    permission_classes = [CanAddTransaction]
    queryset = Transaction.objects.all()
