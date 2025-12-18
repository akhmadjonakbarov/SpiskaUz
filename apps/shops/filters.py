import django_filters

from apps.orders.models import Order


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
