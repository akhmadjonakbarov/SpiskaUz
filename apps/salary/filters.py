import django_filters
from .models import SalaryTransaction

import django_filters
from .models import SalaryTransaction


class SalaryTransactionFilter(django_filters.FilterSet):
    # ---- Amount ----
    min_amount = django_filters.NumberFilter(
        field_name="amount", lookup_expr="gte"
    )
    max_amount = django_filters.NumberFilter(
        field_name="amount", lookup_expr="lte"
    )

    # ---- Paid date ----
    date_paid_from = django_filters.DateFilter(
        field_name="date_paid", lookup_expr="date__gte"
    )
    date_paid_to = django_filters.DateFilter(
        field_name="date_paid", lookup_expr="date__lte"
    )

    # ---- Created date ----
    created_from = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_to = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    # ---- Relations ----
    user_role = django_filters.NumberFilter(field_name="user_role_id")
    shop = django_filters.NumberFilter(field_name="user_role__shop_id")

    # ---- Text ----
    description = django_filters.CharFilter(
        field_name="description", lookup_expr="icontains"
    )

    class Meta:
        model = SalaryTransaction
        fields = [
            "user_role",
            "shop",
            "min_amount",
            "max_amount",
            "date_paid_from",
            "date_paid_to",
            "created_from",
            "created_to",
            "description",
        ]
