from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CashHistory, CashHistoryItem


@admin.register(CashHistory)
class CashHistoryAdmin(ModelAdmin):
    list_display = ("shop", "payment_method", "comment")
    list_filter = ("payment_method",)
    list_display_links = ("shop", "payment_method")
    search_fields = ("shop__name", "comment")


@admin.register(CashHistoryItem)
class CashHistoryItemAdmin(ModelAdmin):
    list_display = ("cash_history", "product_name", "amount", "sale_price", "discount", "product_price")
    list_filter = ("product",)
    list_display_links = ("cash_history", "product_name")
    search_fields = ("cash_history__comment", "product__name")

    def product_name(self, obj):
        return obj.product.name

    product_name.short_description = "Product"
