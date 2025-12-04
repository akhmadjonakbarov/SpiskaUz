from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request

from apps.salary.models import SalaryTransaction
from apps.salary.serializers import SalaryTransactionSerializer


from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

class SalaryTransactionViewSet(viewsets.ModelViewSet):
    queryset = SalaryTransaction.objects.all()
    serializer_class = SalaryTransactionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_role__user__phone', 'user_role__role', 'description']
    ordering_fields = ['date_paid', 'amount']

    @action(detail=True, methods=["get"])
    def get_by_admin(self, request: Request, pk=None):
        """
        Returns salary transactions filtered by admin (user) ID.
        """
        try:
            # Filter salaries where the admin is owner
            transactions = SalaryTransaction.objects.filter(
                user_role__user__id=pk
            )

            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

