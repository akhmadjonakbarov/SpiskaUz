from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.cart.models import Cart, CartItem
from apps.orders.models import OrderPaymentMethod
from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from apps.shops.serializers import ShopSerializer


class AddCartItemSerializer(serializers.Serializer):
    amount = serializers.DecimalField(decimal_places=5, max_digits=50)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )


class ShoppingCartItemSerializer(serializers.ModelSerializer):
    sale_price = serializers.IntegerField(source="product.sale_price", read_only=True)
    sale_price_with_discount = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
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
        model = Cart
        fields = "__all__"


class ConfirmShoppingCartSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
