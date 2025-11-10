
from rest_framework import filters, viewsets

from apps.salary.models import SalaryTransaction
from apps.salary.serializers import SalaryTransactionSerializer


class SalaryTransactionViewSet(viewsets.ModelViewSet):
    queryset = SalaryTransaction.objects.all()
    serializer_class = SalaryTransactionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_role__user__username', 'user_role__role', 'description']
    ordering_fields = ['date_paid', 'amount']
