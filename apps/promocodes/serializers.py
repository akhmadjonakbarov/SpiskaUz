from django.shortcuts import get_object_or_404
from rest_framework import serializers

from apps.cart.models import ShoppingCart

from .models import Promocode, PromocodeItem


class CartField(serializers.CurrentUserDefault):
    def __call__(self, serializer_field):
        return serializer_field.context["view"].kwargs["pk"]


class CreatePromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promocode
        fields = (
            'code', 'value', 'product'
        )

    def create(self, validated_data):
        code = validated_data.get('code')
        value = validated_data.get('value')
        product = validated_data.get('product')

        return Promocode.objects.create(
            code=code, value=value, product=product, shop=product.shop, user=self.context.get("request").user
        )


class PromocodeForProduct(serializers.ModelSerializer):
    class Meta:
        model = Promocode
        fields = (
            'code', 'value'
        )


class PromocodeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromocodeItem
        exclude = ["promocode"]


class PromocodeSerializer(serializers.ModelSerializer):
    # items = PromocodeItemSerializer(many=True, required=False)

    class Meta:
        model = Promocode
        fields = "__all__"

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        promocode = super().create(validated_data)

        try:
            PromocodeItem.objects.bulk_create(
                PromocodeItem(promocode=promocode, **item_data) for item_data in items_data)

        except Exception as e:
            promocode.delete()
            raise serializers.ValidationError({"error": str(e)}) from e

        return promocode


class ApplyPromocodeSerializer(serializers.Serializer):
    current_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    cart = serializers.HiddenField(default=CartField())
    code = serializers.CharField(max_length=256)

    def validate(self, attrs):
        cart = get_object_or_404(ShoppingCart, pk=attrs["cart"])
        promocode = get_object_or_404(Promocode, code=attrs["code"], shop=cart.shop)

        if not promocode.can_use_promocode(attrs["current_user"]):
            raise serializers.ValidationError("Siz ushbu promokoddan allaqachon foydalangansiz.")

        return attrs
