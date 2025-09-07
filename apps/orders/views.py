from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response

from apps.orders.services import OrderService
from common.mixins import ActionPermissionMixin
from common.serializers import EmptyBodySerializer
from utils.convertor import Convertor

from .models import Order, OrderStatus
from .permissions import CanCancelOrder, CanRestoreOrder
from .serializers import CancelAcceptedOrderSerializer, OrderSerializer
from apps.document.models import DocumentOrder, Document, DocumentItemBalance, DocumentItem


class OrderViewSet(
    ActionPermissionMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    queryset = (
        Order.objects.select_related("customer", "admin")
        .prefetch_related(
            "items",
            "items__product__parts",
            "items__product__images",
            "items__product__category",
            "items__product__favorited_by",
            "shop__members",
            "shop__owner",
            "shop__contacts",
            "shop__categories",
        )
        .all()
    )
    permission_classes = [IsAuthenticated]

    order_service = OrderService()

    action_permissions = {
        ("cancel_order",): [CanCancelOrder],
        ("restore_order",): [CanRestoreOrder],
    }

    def list(self, request, *args, **kwargs):
        orders = (Order.objects.select_related("customer", "admin")
                  .prefetch_related(
            "items",
            "items__product__parts",
            "items__product__images",
            "items__product__category",
            "items__product__favorited_by",
            "shop__members",
            "shop__owner",
            "shop__contacts",
            "shop__categories",
        )
                  .filter(
            status='pending' or 'accepted' or 'completed'
        ).all())

    def destroy(self, request, *args, **kwargs):
        """
        Order ni o'chirish uchun
        """
        instance = self.get_object()

        if instance.status == OrderStatus.CANCELLED:
            instance.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            return Response(
                {"error": "Only cancelled orders can be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(["POST"], detail=True, url_path="cancel-order")
    def cancel_order(self, request, pk=None, *args, **kwargs):
        order = self.get_object()

        self.check_object_permissions(request=request, obj=order)

        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            order.save()

            return Response({"message": "Order cancelled successfully."}, status=status.HTTP_200_OK)

        elif order.status == OrderStatus.ACCEPTED:
            order.status = OrderStatus.CANCELLED_BY_ADMIN
            order.save()

            return Response(
                {"message": "Order cancelled by admin successfully."},
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"error": "Order already cancelled or completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(request_body=CancelAcceptedOrderSerializer)
    @action(
        ["PATCH"],
        detail=True,
        url_path="cancel-accepted-order",
        serializer_class=CancelAcceptedOrderSerializer,
    )
    def cancel_accepted_order(self, request, pk=None, *args, **kwargs):
        order = self.get_object()
        self.check_object_permissions(request=request, obj=order)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_status = serializer.validated_data.get("status")

        if order.status != OrderStatus.CANCELLED_BY_ADMIN:
            return Response(
                {"error": "Order is already cancelled or completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.customer != request.user:
            return Response(
                {"error": "You can only modify your own orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if action_status == "accept":
            order.status = OrderStatus.CANCELLED
            document_order = DocumentOrder.objects.get(order=order)
            document: Document = document_order.document
            for di in document.document_items.all():
                document_item: DocumentItem = di
                balance = DocumentItemBalance.objects.filter(
                    income_price=document_item.income_price, sale_price=document_item.sale_price,
                    product=document_item.product,
                ).first()
                if balance:
                    balance.qty = balance.qty + Convertor.to_decimal(document_item.qty)
                    balance.save()
                else:
                    new_document = Document.objects.create(
                        doc_type='buy', shop=document.shop, user=document.user,
                    )
                    new_document_item = DocumentItem.objects.create(
                        document=new_document,
                        shop=document.shop, user=document.user,
                        qty=document_item.qty, income_price=document_item.income_price,
                        sale_price=document_item.sale_price, profit_as_percent=document_item.profit_as_percent,
                        product=document_item.product,
                        currency_rate=document_item.currency_rate,
                        currency_rate_value=document_item.currency_rate_value,
                    )
                    DocumentItemBalance.objects.create(
                        document=new_document,
                        shop=document.shop, user=document.user,
                        qty=new_document_item.qty, income_price=new_document_item.income_price,
                        sale_price=new_document_item.sale_price, profit_as_percent=new_document_item.profit_as_percent,
                        product=new_document_item.product, document_item=new_document_item,
                        currency_rate=new_document_item.currency_rate,
                        currency_rate_value=new_document_item.currency_rate_value,
                    )

            order.save()
            return Response(
                {"message": "Accepted order has been cancelled."},
                status=status.HTTP_200_OK,
            )
        else:
            order.status = OrderStatus.ACCEPTED
            order.save()
            return Response(
                {"message": "Order status reverted to 'accepted'."},
                status=status.HTTP_200_OK,
            )

    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(["POST"], detail=True, url_path="restore-order")
    def restore_order(self, request, pk=None, *args, **kwargs):
        """
        Bekor qilingan order ni savatga qaytarish
        """

        order = self.get_object()

        self.check_object_permissions(request=request, obj=order)

        if order.status == OrderStatus.CANCELLED:
            self.order_service.restore_order(user=request.user, order=order)

            return Response(
                {"message": "Order restored to cart successfully."},
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"error": "Order cannot be restored."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(["POST"], detail=True)
    def complete(self, request, pk=None, *args, **kwargs):
        """
        Order ni tasdiqlash uchun api
        """

        order = self.get_object()

        is_confirmed = self.order_service.complete_order(order, request.user)

        if is_confirmed:
            return Response({"message": "Order confirmed successfully."}, status=status.HTTP_200_OK)

        return Response(
            {"message": "Order confirmation failed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(["POST"], detail=True)
    def accept(self, request, pk=None, *args, **kwargs):
        order = self.get_object()

        result = self.order_service.accept_order(order, request.user)

        if result:
            return Response(
                {"message": "Order status successfully updated to 'processing'."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "message": "Failed to update order status to 'processing'. It may already be in that state or invalid transition."},
            status=status.HTTP_400_BAD_REQUEST,
        )
