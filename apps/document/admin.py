from django.contrib import admin
from .models import Document, DocumentItem, DocumentItemBalance, PaymentInfo, PaymentDetail
from ..base.admin import BaseAdmin


@admin.register(PaymentInfo)
class YourModelAdmin(BaseAdmin):
    list_display = (
        'id',
        'get_document_type',
        'get_shop_name',
        'note',
        'payed_money',
        'un_payed_money',
        'currency_type',
    )
    list_select_related = ('document__shop',)

    def get_shop_name(self, obj):
        return obj.document.shop.name

    def get_document_type(self, obj):
        return obj.document.doc_type

    get_shop_name.short_description = 'Shop'
    get_document_type.short_description = 'Document Type'


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = (
        'id', 'doc_type', 'shop', 'user'
    )


class BaseDocumentItemAdmin(BaseAdmin):
    list_display = (
        'id', 'get_product_name', 'sale_price', 'income_price',
        'qty', 'get_currency_type', 'currency_rate_value', 'get_product_status', 'profit_as_percent', 'shop'
    )


@admin.register(DocumentItem)
class DocumentItemAdmin(BaseDocumentItemAdmin):
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
class DocumentItemBalanceAdmin(BaseDocumentItemAdmin):
    list_display = (
        'id', 'get_product_name', 'sale_price', 'income_price',
        'qty', 'get_currency_type', 'currency_rate_value', 'profit_as_percent', 'shop'
    )

    @admin.display(description='Product Name')
    def get_product_name(self, obj):
        return obj.product.name

    @admin.display(description='Currency Type')
    def get_currency_type(self, obj):
        return obj.product.currency_type


@admin.register(PaymentDetail)
class PaymentDetailAdmin(BaseAdmin):
    list_display = (
        'id',
        'get_document_type',
        'get_shop_name',
        'note',
        'payment_method',
    )
    list_select_related = ('document__shop',)

    def get_shop_name(self, obj):
        return obj.document.shop.name

    def get_document_type(self, obj):
        return obj.document.doc_type

    get_shop_name.short_description = 'Shop'
    get_document_type.short_description = 'Document Type'
