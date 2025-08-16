from django.contrib import admin
from .models import Document, DocumentItem, DocumentItemBalance, PaymentInfo, PaymentDetail
from ..base.admin import BaseAdmin


@admin.register(PaymentInfo)
class PaymentInfoAdmin(BaseAdmin):
    pass


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = (
        'doc_type',
    )


@admin.register(DocumentItem)
class DocumentItemAdmin(BaseAdmin):
    list_display = (
        'id', 'get_product_name', 'sale_price', 'income_price',
        'qty', 'get_currency_type', 'currency_rate_value', 'get_product_status'
    )
    list_filter = ('document__doc_type', 'product__currency_type',)

    @admin.display(description='Currency Type')
    def get_currency_type(self, obj):
        return obj.product.currency_type

    @admin.display(description="Status")
    def get_product_status(self, obj):  # Removed incorrect type
        return obj.document.doc_type

    @admin.display(description='Product Name')
    def get_product_name(self, obj):
        return obj.product.name


@admin.register(DocumentItemBalance)
class DocumentItemBalanceAdmin(BaseAdmin):
    list_display = (
        'id', 'get_product_name', 'sale_price', 'income_price',
        'qty', 'get_currency_type', 'currency_rate_value',
    )

    @admin.display(description='Product Name')
    def get_product_name(self, obj):
        return obj.product.name

    @admin.display(description='Currency Type')
    def get_currency_type(self, obj):
        return obj.product.currency_type


@admin.register(PaymentDetail)
class PaymentDetailAdmin(BaseAdmin):
    pass
