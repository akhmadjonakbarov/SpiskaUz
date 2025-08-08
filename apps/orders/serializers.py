from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.serializers import ProductSerializer
from apps.users.serializers import UserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    admin = UserSerializer(read_only=True)
    customer = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"


class CancelAcceptedOrderSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("accept", "Accept"), ("cancel", "Cancel")], required=True)
