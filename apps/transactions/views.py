from rest_framework import viewsets

from .models import Transaction
from .permissions import CanAddTransaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [CanAddTransaction]
    queryset = Transaction.objects.all()
