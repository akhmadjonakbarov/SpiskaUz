from itertools import product

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from apps.orders.models import Order, OrderStatus, OrderItem
from apps.orders.serializers import OrderSerializer
from apps.orders.services import OrderService
from apps.promocodes.serializers import ApplyPromocodeSerializer
from utils.convertor import Convertor
from .models import PromoCode, Cart, CartItem
from .permissions import CanConfirmCartPermission, CanEditCartItemPermission
from .serializers import ConfirmShoppingCartSerializer, ShoppingCartItemSerializer, ShoppingCartSerializer, \
    AddCartItemSerializer
from ..products.models import Product


class ShoppingCartItemViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin,
                              mixins.DestroyModelMixin):
    serializer_class = ShoppingCartItemSerializer
    queryset = CartItem.objects.all()
    permission_classes = [CanEditCartItemPermission]

    @swagger_auto_schema(
        request_body=AddCartItemSerializer
    )
    def create(self, request, *args, **kwargs):
        amount = request.data.get('amount', 0.0)
        product_id = request.data.get('product')
        product = Product.objects.get(id=product_id)
        user = request.user

        cart = Cart.objects.filter(user=user, shop=product.shop).first()

        if not cart:
            cart = Cart.objects.create(
                user=user, shop=product.shop
            )
        cart_item = self.get_queryset().filter(cart__user=user, cart__shop=product.shop, product=product).first()

        if cart_item:
            cart_item.amount += Convertor.to_decimal(amount)
            cart_item.save()
        else:
            CartItem.objects.create(
                cart=cart, product=product, amount=Convertor.to_decimal(amount)
            )
        return Response(
            ShoppingCartSerializer(cart, many=False)
            .data,
        )

    # def perform_create(self, serializer):
    #     validated_data = serializer.validated_data
    #     user = self.request.user
    #     product = validated_data["product"]
    #
    #     cart = Cart.objects.filter(user=user, shop=product.shop).first()
    #
    #     if not cart:
    #         cart = Cart.objects.create(
    #             user=user, shop=product.shop
    #         )
    #     cart_item = self.get_queryset().filter(cart__user=user, cart__shop=product.shop, product=product).first()
    #
    #     if cart_item:
    #         cart_item.amount += validated_data["amount"]
    #         cart_item.save()
    #         serializer.instance = cart_item
    #
    #     else:
    #         CartItem.objects.create(
    #             cart=cart, product=product, amount=validated_data['amount']
    #         )


class ShoppingCartViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = Cart.objects.all()
    permission_classes = [CanEditCartItemPermission]

    order_service = OrderService()

    @swagger_auto_schema(request_body=ConfirmShoppingCartSerializer)
    @action(detail=True, methods=["POST"], url_path="create-order", permission_classes=[CanConfirmCartPermission])
    def create_order(self, request: Request, pk):
        cart = self.get_object()
        cart_items = CartItem.objects.filter(cart=cart)

        comment = request.data.get("comment", None)
        try:
            with transaction.atomic():
                order: Order = Order.objects.create(
                    customer=cart.user,
                    shop=cart.shop,
                    status=OrderStatus.PENDING,
                    comment=comment
                )
                for ci in cart_items:
                    cart_item: CartItem = ci
                    OrderItem.objects.create(
                        order=order, product=cart_item.product, amount=cart_item.amount
                    )

            serializer = OrderSerializer(order, context={"request": request})

            return Response(data={
                'message': f'Order#{order.id} created successfully',
                'order': OrderSerializer(order, many=False).data
            }, status=201
            )
        except Exception as e:
            print(e)
            return Response(
                data={
                    'error': str(e)
                }
            )

    @swagger_auto_schema(request_body=ApplyPromocodeSerializer)
    @action(detail=True, methods=["POST"], url_path="apply-promocode", serializer_class=ApplyPromocodeSerializer)
    def apply_promocode(self, request, pk=None):
        cart = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart.promocode = PromoCode.objects.get(code=serializer.validated_data["code"])
        cart.save()

        return Response({"message": "Promocode savatga muvaffaqqiyatli biriktirildi"}, status=200)
