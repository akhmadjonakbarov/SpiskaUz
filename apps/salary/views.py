from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, viewsets
from rest_framework.request import Request
from apps.salary.models import SalaryTransaction
from apps.salary.serializers import SalaryTransactionSerializer, CreateSalaryTransaction

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class SalaryTransactionViewSet(viewsets.ModelViewSet):
    queryset = SalaryTransaction.actives.all()
    serializer_class = SalaryTransactionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_role__user__phone',
                     'user_role__role', 'description', 'shop']
    ordering_fields = ['date_paid', 'amount']

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'GET':
            serializer_class = SalaryTransactionSerializer
        else:
            serializer_class = CreateSalaryTransaction

        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

        # Define manual parameters

    list_params = [
        openapi.Parameter(
            'min_amount',
            openapi.IN_QUERY,
            description="minimum amount (>=)", type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'max_amount',
            openapi.IN_QUERY, description="maximum amount (<=)",
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'date_from', openapi.IN_QUERY, description="date_paid from (YYYY-MM-DD)",
            type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            'date_to', openapi.IN_QUERY, description="date_paid to (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            'description', openapi.IN_QUERY, description="filter by description (icontains)",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'shop', openapi.IN_QUERY, description="filter by user_role.shop id",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'search', openapi.IN_QUERY, description="DRF search (phone, role, description)",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'ordering', openapi.IN_QUERY, description="ordering, e.g. amount or -date_paid",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY, description="page number (if using pagination)",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'role', openapi.IN_QUERY, description="filtering transactions by role(id)",
            type=openapi.TYPE_INTEGER
        ),
    ]

    @swagger_auto_schema(manual_parameters=list_params, responses={200: SalaryTransactionSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        qs = super().get_queryset()

        # --- Extra filters ---
        min_amount = request.query_params.get("min_amount")
        max_amount = request.query_params.get("max_amount")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        description = request.query_params.get("description")
        shop = request.query_params.get("shop")
        role = request.query_params.get("role")

        if min_amount:
            qs = qs.filter(amount__gte=min_amount)

        if shop:
            qs = qs.filter(user_role__shop_id=shop)

        if max_amount:
            qs = qs.filter(amount__lte=max_amount)

        if description:
            qs = qs.filter(description__icontains=description)

        if date_from:
            qs = qs.filter(date_paid__date__gte=date_from)

        if date_to:
            qs = qs.filter(date_paid__date__lte=date_to)

        if role:
            qs = qs.filter(user_role_id=role)

        # --- Apply DRF Search + Ordering ---
        for backend in self.filter_backends:
            qs = backend().filter_queryset(request, qs, self)

        # Serialize
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        instance = get_object_or_404(self.queryset, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def get_by_admin(self, request: Request, pk=None):
        """
        Returns salary transactions filtered by admin (user) ID.
        """
        try:
            # Filter salaries where the admin is owner
            transactions = SalaryTransaction.objects.filter(
                user_role_id=pk
            )

            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
