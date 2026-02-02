import django_filters

from apps.shops.models import Shop


class ShopFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains"
    )

    class Meta:
        model = Shop
        fields = ["search"]
