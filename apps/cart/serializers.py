from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.cart.models import ShoppingCart, ShoppingCartItem
from apps.orders.models import OrderPaymentMethod
from apps.products.serializers import ProductSerializer
from apps.shops.serializers import ShopSerializer


class ShoppingCartItemSerializer(serializers.ModelSerializer):
    sale_price = serializers.IntegerField(source="product.sale_price", read_only=True)
    sale_price_with_discount = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShoppingCartItem
        exclude = ["cart"]

    def to_representation(self, instance):
        value = super().to_representation(instance)
        value["amount"] = float(instance.amount)
        value["product"] = ProductSerializer(instance.product, context={"request": self.context.get("request")}).data

        return value


class ShoppingCartSerializer(serializers.ModelSerializer):
    items = ShoppingCartItemSerializer(many=True)
    shop = ShopSerializer()

    class Meta:
        model = ShoppingCart
        fields = "__all__"


class ConfirmShoppingCartSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=OrderPaymentMethod.choices)
    paid_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate_paid_amount(self, value):
        cart: ShoppingCart = self.instance

        if value > cart.calc_total_price():
            raise ValidationError("The value must be less than the total price.")

        return value
