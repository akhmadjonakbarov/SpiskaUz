from apps.document.models import Document
from apps.orders.models import Order
from apps.shops.models import ShopBalanceTransaction
import django_filters
from django_filters import rest_framework as filters


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class OrderFilter(django_filters.FilterSet):
    status = CharInFilter(field_name="status", lookup_expr="in")
    customer = django_filters.CharFilter(field_name="customer_id")
    from_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="Created date from (YYYY-MM-DD)",
    )
    to_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="Created date to (YYYY-MM-DD)",
    )

    class Meta:
        model = Order
        fields = [
            "status", "customer",
            "from_date",
            "to_date",
        ]


class ShopBalanceTransactionFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="Created date from (YYYY-MM-DD)",
    )
    to_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="Created date to (YYYY-MM-DD)",
    )

    transaction_type = django_filters.CharFilter(
        method="filter_transaction_type",
        label="Transaction type (income | outcome)",
    )

    class Meta:
        model = ShopBalanceTransaction
        fields = [
            "kind",
            "transaction_type",
            "from_date",
            "to_date",
        ]

    def filter_transaction_type(self, queryset, name, value):
        income_kinds = ['profit', 'cash_income', 'cash_profit']

        if value == 'income':
            return queryset.filter(kind__in=income_kinds)
        elif value == 'outcome':
            return queryset.exclude(kind__in=income_kinds)

        return queryset


class DocumentFilter(django_filters.FilterSet):
    doc_type = django_filters.CharFilter(field_name="doc_type")
    user_id = django_filters.CharFilter(field_name="user")
    from_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="Created date from (YYYY-MM-DD)",
    )
    to_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="Created date to (YYYY-MM-DD)",
    )

    class Meta:
        model = Document
        fields = [
            "doc_type",
            "from_date",
            "to_date",
            "user_id"
        ]
