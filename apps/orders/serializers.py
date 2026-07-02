from decimal import Decimal
from rest_framework import serializers
from apps.orders.models import Order, OrderItem, OrderPaymentDetail
from apps.products.serializers import ProductSerializer
from apps.users.serializers import UserSerializer
from utils.convertor import Convertor


class OrderPaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPaymentDetail
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    admin = UserSerializer(read_only=True)
    customer = UserSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    payment_detail = OrderPaymentDetailSerializer()

    class Meta:
        model = Order
        fields = "__all__"

    def get_total_price(self, order: Order):
        from apps.document.models import DocumentItemBalance
        total_price = Decimal('0.0')

        for item in order.items.all():
            order_item: OrderItem = item
            balance = DocumentItemBalance.objects.filter(
                product=order_item.product, shop=order.shop
            ).first()

            if balance is not None:
                if order_item.product.currency_type.lower() in 'usd':
                    converted_price = Convertor.to_decimal(balance.sale_price) * Convertor.to_decimal(
                        balance.currency_rate_value)
                    total_price = total_price + converted_price * Convertor.to_decimal(order_item.amount)
                else:
                    total_price = total_price + Convertor.to_decimal(balance.sale_price) * Convertor.to_decimal(
                        order_item.amount)
            else:
                total_price = total_price + Convertor.to_decimal(order_item.product.sale_price) * Convertor.to_decimal(
                    order_item.amount)
        return total_price


class CancelAcceptedOrderSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("accept", "Accept"), ("cancel", "Cancel")], required=True)
