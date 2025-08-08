from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from apps.orders.services import OrderService
from apps.promocodes.serializers import ApplyPromocodeSerializer

from .models import Promocode, ShoppingCart, ShoppingCartItem
from .permissions import CanConfirmCartPermission, CanEditCartItemPermission
from .serializers import ConfirmShoppingCartSerializer, ShoppingCartItemSerializer, ShoppingCartSerializer


class ShoppingCartItemViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    serializer_class = ShoppingCartItemSerializer
    queryset = ShoppingCartItem.objects.all()
    permission_classes = [CanEditCartItemPermission]

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        user = self.request.user
        product = validated_data["product"]

        cart, _ = ShoppingCart.objects.get_or_create(user=user, shop=product.shop)

        cart_item = self.get_queryset().filter(cart__user=user, cart__shop=product.shop, product=product).first()

        if cart_item:
            cart_item.amount += validated_data["amount"]
            cart_item.save()
            serializer.instance = cart_item

        else:
            serializer.save(cart=cart)


class ShoppingCartViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    permission_classes = [CanEditCartItemPermission]

    order_service = OrderService()

    @swagger_auto_schema(request_body=ConfirmShoppingCartSerializer)
    @action(detail=True, methods=["POST"], url_path="confirm-order", permission_classes=[CanConfirmCartPermission])
    def create_order(self, request, pk):
        cart = self.get_object()

        serializer = ConfirmShoppingCartSerializer(instance=cart, data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_method = serializer.validated_data["payment_method"]
        paid_amount = serializer.validated_data["paid_amount"]
        comment = serializer.validated_data.get("comment", "")

        order: Order = self.order_service.create_order_from_cart(
            cart,
            payment_method=payment_method,
            comment=comment,
            paid_amount=paid_amount,
        )

        serializer = OrderSerializer(order, context={"request": request})

        return Response(serializer.data, status=201)

    @swagger_auto_schema(request_body=ApplyPromocodeSerializer)
    @action(detail=True, methods=["POST"], url_path="apply-promocode", serializer_class=ApplyPromocodeSerializer)
    def apply_promocode(self, request, pk=None):
        cart = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart.promocode = Promocode.objects.get(code=serializer.validated_data["code"])
        cart.save()

        return Response({"message": "Promocode savatga muvaffaqqiyatli biriktirildi"}, status=200)
