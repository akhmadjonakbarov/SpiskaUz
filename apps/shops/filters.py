import django_filters

from apps.document.models import Document
from apps.orders.models import Order
from apps.shops.models import ShopBalanceTransaction


class OrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    customer = django_filters.CharFilter(field_name="customer_id")
    created_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Order
        fields = [
            "status", "customer",
            "created_from",
            "created_to",
        ]


class ShopBalanceTransactionFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = ShopBalanceTransaction
        fields = [
            "amount",
            "created_from",
            "created_to",
        ]


class DocumentFilter(django_filters.FilterSet):
    doc_type = django_filters.CharFilter(field_name="doc_type")
    created_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Document
        fields = [
            "doc_type",
            "created_from",
            "created_to",
        ]
