from rest_framework import serializers
from decimal import Decimal
from .models import Document, PromoCode


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"


class DocumentItemSerializer(serializers.Serializer):
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
    products = DocumentItemSerializer(many=True)
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
