import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains"
    )
    shop_id = django_filters.CharFilter(
        field_name="shop_id", lookup_expr="icontains"
    )
    barcode = django_filters.CharFilter(
        field_name="barcode", lookup_expr="icontains"
    )

    class Meta:
        model = Product
        fields = [
            "name", "shop_id", "barcode"
        ]
