from django.db.models import Q
from django_filters import rest_framework as filters

from apps.products.models import Product


class ProductFilter(filters.FilterSet):
    search = filters.CharFilter(method="search_filter", label="Search")

    class Meta:
        model = Product
        fields = ["name", "barcode", "description", "category", "is_selected", "is_active"]

    def search_filter(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value) | Q(barcode__icontains=value) | Q(category__name__icontains=value))
