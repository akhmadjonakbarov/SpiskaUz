from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem, OrderPaymentDetail, ProductOrderItemInfo


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = (
        "id", "order", "product", "amount"
    )
    list_filter = (
        "order", "product"
    )


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 1
    min_num = 1


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id", "customer", "shop", "admin", "discount", "status",
        "created_at", "updated_at"
    )
    list_filter = ("customer", "shop")
    inlines = [OrderItemInline]


@admin.register(OrderPaymentDetail)
class OrderPaymentDetailAdmin(ModelAdmin):
    list_display = (
        'order', 'payed', 'un_payed', 'payment_method'
    )
