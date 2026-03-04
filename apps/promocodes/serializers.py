from django.shortcuts import get_object_or_404
from rest_framework import serializers

from apps.cart.models import Cart

from .models import PromoCode, PromoCodeItem
from ..products.models import Product
from ..shops.models import Shop


class CartField(serializers.CurrentUserDefault):
    def __call__(self, serializer_field):
        return serializer_field.context["view"].kwargs["pk"]


class PromoCodeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCodeItem
        exclude = ["promo_code"]


class PromoCodeSerializer(serializers.ModelSerializer):
    # items = PromoCodeItemSerializer(many=True, required=False)

    class Meta:
        model = PromoCode
        fields = "__all__"


class PromoCodeCreateItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    discount = serializers.DecimalField(max_digits=20, decimal_places=5)


class PromoCodeCreateSerializer(serializers.Serializer):
    items = PromoCodeCreateItemSerializer(many=True, required=False)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())


class ApplyPromoCodeSerializer(serializers.Serializer):
    current_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    cart = serializers.HiddenField(default=CartField())
    code = serializers.CharField(max_length=256)

    def validate(self, attrs):
        cart = get_object_or_404(Cart, pk=attrs["cart"])
        promo_code = get_object_or_404(PromoCode, code=attrs["code"], shop=cart.shop)

        if not promo_code.can_use_promo_code(attrs["current_user"]):
            raise serializers.ValidationError("Siz ushbu promokoddan allaqachon foydalangansiz.")

        return attrs


class PromoCodeItemSearchSerializer(serializers.Serializer):
    promo_code = serializers.CharField(max_length=256)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
