from rest_framework import serializers
from decimal import Decimal
from .models import Document, PromoCode, DocumentItem


class DocumentItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    currency_rate = serializers.SerializerMethodField()

    class Meta:
        model = DocumentItem
        fields = "__all__"

    def get_product(self, obj: DocumentItem):
        from apps.products.serializers import ProductSerializer
        product = obj.product
        return ProductSerializer(product, many=False).data

    def get_currency_rate(self, obj):
        from apps.currency_rate.serializers import CurrencyRateSerializer
        return CurrencyRateSerializer(obj.currency_rate, many=False).data


class DocumentSerializer(serializers.ModelSerializer):
    document_items = DocumentItemSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = "__all__"


class DocumentSerializerForStatistic(serializers.ModelSerializer):
    document_items = DocumentItemSerializer(many=True, read_only=True)
    admin = serializers.SerializerMethodField()
    supplier = serializers.SerializerMethodField()
    total_sale = serializers.SerializerMethodField()
    total_income = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()

    class Meta:
        model = Document
        exclude = ('user',)

    def get_admin(self, document: Document):
        from apps.users.serializers import UserSerializer
        return UserSerializer(document.user, many=False).data

    def get_supplier(self, document: Document):
        from apps.supplier.serializers import SupplierSerializer
        if document.supplier is None:
            return None
        return SupplierSerializer(document.supplier, many=False).data

    def get_total_sale(self, document: Document):
        total_price = Decimal('0.0')
        for document_item in document.document_items.all():
            item: DocumentItem = document_item
            if item.product.currency_type == 'usd':
                total_price = total_price + Decimal(item.sale_price) * Decimal(item.currency_rate_value) * Decimal(
                    item.qty)
            else:
                total_price = total_price + Decimal(item.sale_price) * Decimal(item.qty)
        return total_price

    def get_total_income(self, document: Document):
        total_price = Decimal('0.0')
        for document_item in document.document_items.all():
            item: DocumentItem = document_item
            if item.product.currency_type == 'usd':
                total_price = total_price + Decimal(item.income_price) * Decimal(item.currency_rate_value) * Decimal(
                    item.qty)
            else:
                total_price = total_price + Decimal(item.income_price) * Decimal(item.qty)

        return total_price

    def get_total_discount(self, document: Document):
        if document.doc_type == 'sell':
            return document.payment_detail.discount
        else:
            return Decimal('0.0')

    def get_total_debt(self, document: Document):
        pass


class SaleItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=20, decimal_places=5)


class BuyProductSerializer(serializers.Serializer):
    product_part_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    note = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    payed_money = serializers.DecimalField(max_digits=15, decimal_places=5, default=Decimal("0.0"))
    un_payed_money = serializers.DecimalField(max_digits=15, decimal_places=5, default=Decimal("0.0"))
    supplier_id = serializers.IntegerField()


class ClientDebtSerializer(serializers.Serializer):
    from apps.users.models import User
    paid_money = serializers.DecimalField(max_digits=50, decimal_places=5, default=Decimal('0.0'))
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )


class SellProductSerializer(serializers.Serializer):
    """
    Serializer for handling product sales input.

    Fields:
        products (list): A list of products being sold, including quantity and product ID.
        discount (Decimal): An optional manual discount amount to apply to the total.
        payment_type (str): The method of payment (e.g., 'cash', 'card').
        promo_code (int, optional): ID of an optional promo code for discount.
        note (str): Optional comment related to the sale.
    """
    products = SaleItemSerializer(many=True)
    discount = serializers.DecimalField(max_digits=15, decimal_places=5, default=Decimal("0.0"))
    payment_method = serializers.CharField()
    promo_code = serializers.PrimaryKeyRelatedField(
        queryset=PromoCode.objects.all(),
        required=False,
        allow_null=True
    )
    note = serializers.CharField(max_length=1500)
    debt = ClientDebtSerializer(
        required=False
    )
