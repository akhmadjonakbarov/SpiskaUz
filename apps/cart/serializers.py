from decimal import Decimal
from rest_framework import serializers
from apps.cart.models import Cart, CartItem
from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from utils.convertor import Convertor


class AddCartItemSerializer(serializers.Serializer):
    amount = serializers.DecimalField(decimal_places=5, max_digits=50)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False)

    class Meta:
        model = CartItem
        exclude = ["cart"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = "__all__"

    def get_total_price(self, cart: Cart):
        from apps.document.models import DocumentItemBalance
        total_price = Decimal('0.0')

        for item in cart.items.all():
            cart_item: CartItem = item
            balance = DocumentItemBalance.objects.filter(
                product=cart_item.product, shop=cart.shop
            ).first()

            if cart_item.product.currency_type.lower() in 'usd':
                converted_price = Convertor.to_decimal(balance.sale_price) * Convertor.to_decimal(
                    balance.currency_rate_value)
                total_price = total_price + converted_price * Convertor.to_decimal(cart_item.amount)
            else:
                total_price = total_price + Convertor.to_decimal(balance.sale_price) * Convertor.to_decimal(
                    cart_item.amount)
        return total_price


class ConfirmShoppingCartSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
