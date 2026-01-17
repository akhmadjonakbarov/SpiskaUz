from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, viewsets
from rest_framework.request import Request

from apps.base.paginations import PageSizePagination
from apps.salary.models import SalaryTransaction
from apps.salary.serializers import SalaryTransactionSerializer, CreateSalaryTransaction
from .filters import SalaryTransactionFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class SalaryTransactionViewSet(viewsets.ModelViewSet):
    queryset = SalaryTransaction.actives.all()
    pagination_class = PageSizePagination

    # ---- Filters ----
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SalaryTransactionFilter

    search_fields = [
        "user_role__user__phone",
        "user_role__role",
        "description",
        "user_role__shop__name",
    ]

    ordering_fields = ["date_paid", "amount", "created_at"]
    ordering = ["-date_paid"]  # default ordering

    # ---- Serializer switch ----
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CreateSalaryTransaction
        return SalaryTransactionSerializer

    # ---- Swagger parameters ----
    swagger_filter_params = [
        openapi.Parameter(
            "user_role", openapi.IN_QUERY,
            description="Filter by user_role ID",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            "shop", openapi.IN_QUERY,
            description="Filter by shop ID",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            "min_amount", openapi.IN_QUERY,
            description="Minimum amount (>=)",
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            "max_amount", openapi.IN_QUERY,
            description="Maximum amount (<=)",
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            "date_paid_from", openapi.IN_QUERY,
            description="Paid date from (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            "date_paid_to", openapi.IN_QUERY,
            description="Paid date to (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            "created_from", openapi.IN_QUERY,
            description="Created date from (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            "created_to", openapi.IN_QUERY,
            description="Created date to (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            "description", openapi.IN_QUERY,
            description="Filter by description (icontains)",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            "search", openapi.IN_QUERY,
            description="Search (phone, role, description)",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            "ordering", openapi.IN_QUERY,
            description="Ordering, e.g. amount or -date_paid",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            "page", openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER
        ),
    ]

    @swagger_auto_schema(
        manual_parameters=swagger_filter_params,
        responses={200: SalaryTransactionSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def destroy(self, request, pk=None):
        instance = self.get_object()
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
