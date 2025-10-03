from decimal import Decimal

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from apps.orders.models import Order, OrderStatus, OrderItem, OrderPaymentDetail
from apps.orders.serializers import OrderSerializer
from apps.orders.services import OrderService
from apps.promocodes.serializers import ApplyPromocodeSerializer
from utils.convertor import Convertor
from .models import PromoCode, Cart, CartItem
from .permissions import CanConfirmCartPermission, CanEditCartItemPermission
from .serializers import ConfirmShoppingCartSerializer, CartItemSerializer, CartSerializer, \
    CreateOrUpdateCartItemSerializer
from apps.products.models import Product
from ..currency_rate.models import CurrencyRate
from ..customer_transaction.models import CustomerTransaction


class CartItemViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin,
    mixins.DestroyModelMixin
):
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.all()
    permission_classes = [CanEditCartItemPermission, IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ["POST", "PATCH"]:
            return CreateOrUpdateCartItemSerializer(*args, **kwargs)
        return CartItemSerializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        cart_item = self.get_object()

        # ✅ extract and validate "amount"
        amount = request.data.get("amount")
        if amount is None:
            raise ValidationError({"amount": "This field is required."})
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            raise ValidationError({"amount": "Must be an integer."})
        if amount < 0:
            raise ValidationError({"amount": "Must be greater than or equal to 0."})

        # ✅ save after validation
        cart_item.amount = amount
        cart_item.save()

        return Response(
            data={
                "detail": CartItemSerializer(cart_item).data
            },
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        try:
            amount = request.data.get('amount', 0.0)
            product_id = request.data.get('product')
            product = Product.objects.get(id=product_id)
            user = request.user

            cart = Cart.objects.filter(customer=user, shop=product.shop).first()

            if not cart:
                cart = Cart.objects.create(
                    customer=user, shop=product.shop
                )
            cart_item = self.get_queryset().filter(
                cart__customer=user, cart__shop=product.shop,
                product=product,
            ).first()

            if cart_item:
                cart_item.amount += Convertor.to_decimal(amount)
                cart_item.save()
            else:
                CartItem.objects.create(
                    cart=cart, product=product, amount=Convertor.to_decimal(amount)
                )
            return Response(
                CartSerializer(cart, many=False)
                .data,
            )
        except Exception as e:
            return Response(
                data={
                    "error": str(e)
                }
            )


class CartViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    permission_classes = [IsAuthenticated, ]

    order_service = OrderService()

    def list(self, request, *args, **kwargs):
        carts = self.get_queryset().filter(
            customer=request.user
        )
        serializer_data = CartSerializer(carts, many=True).data
        return Response(
            data=serializer_data
        )

    @swagger_auto_schema(request_body=ConfirmShoppingCartSerializer)
    @action(detail=True, methods=["POST"], url_path="create-order", permission_classes=[CanConfirmCartPermission])
    def create_order(self, request: Request, pk):
        cart = self.get_object()
        cart_items = CartItem.objects.filter(cart=cart)

        comment = request.data.get("comment", None)
        payment_type = request.data.get("payment_type", Decimal('0.0'))
        un_payed = request.data.get("un_payed", Decimal('0.0'))
        payed = request.data.get("payed", Decimal('0.0'))
        discount = request.data.get("discount", Decimal('0.0'))
        try:
            with transaction.atomic():
                order: Order = Order.objects.create(
                    customer=cart.customer,
                    shop=cart.shop,
                    status=OrderStatus.PENDING,
                    comment=comment, discount=discount
                )
                OrderPaymentDetail.objects.create(
                    payed=payed,
                    un_payed=un_payed,
                    payment_method=payment_type,
                    order=order
                )
                if un_payed > Decimal('0.0'):
                    latest_currency = CurrencyRate.objects.filter(shop=cart.shop).order_by('-created_at').first()
                    CustomerTransaction.objects.create(
                        shop=cart.shop,
                        order=order,
                        transaction_type='debt', amount=un_payed, customer=request.user,
                        currency_rate=latest_currency.rate
                    )
                for ci in cart_items:
                    cart_item: CartItem = ci
                    OrderItem.objects.create(
                        order=order, product=cart_item.product, amount=cart_item.amount
                    )

            serializer = OrderSerializer(order, context={"request": request})
            cart.delete()

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
