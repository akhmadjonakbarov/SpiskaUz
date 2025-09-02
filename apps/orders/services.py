from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.cart.models import Cart
from apps.notifications.models import Notification, NotificationType
from apps.users.models import User

from .models import Order, OrderItem, OrderPaymentMethod, OrderStatus


class OrderService:
    def _create_notification(self, user, shop, notif_type, order):
        Notification.objects.create(
            user=user,
            shop=shop,
            type=notif_type,
            order=order,
        )

    def _assert_order_status(self, order, allowed_statuses):
        if order.status not in allowed_statuses:
            raise ValidationError({"error": f"Order must be in one of {allowed_statuses}."})

    @transaction.atomic
    def create_order_from_cart(self, cart: Cart, payment_method=OrderPaymentMethod.CASH, **kwargs) -> Order:
        cart_items = cart.items.select_related("product")

        if not cart_items.exists():
            raise ValueError("Savat bo‘sh, buyurtma yaratib bo‘lmaydi.")

        total_price = Decimal("0.00")
        order_items = []

        order = Order.objects.create(
            customer=cart.user,
            shop=cart.shop,
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            **kwargs,
        )

        for item in cart_items:
            price = item.sale_price_with_discount()
            item_total = item.amount * price
            total_price += item_total

            order_items.append(OrderItem(order=order, product=item.product, amount=item.amount, price=price))

        OrderItem.objects.bulk_create(order_items)

        order.total_price = total_price
        order.agreed_price = total_price
        order.debt = total_price - order.paid_amount
        order.save()

        cart.items.all().delete()

        self._create_notification(order.customer, order.shop, NotificationType.ORDER_EVENT_ADMIN, order)

        return order

    def restore_order(self, user: User, order: Order):
        cart, _ = Cart.objects.get_or_create(user=user, shop=order.shop)

        for item in order.items.select_related("product"):
            cart.items.get_or_create(product=item.product, amount=item.amount)

        order.delete()

    def complete_order(self, order: Order, admin: User):
        self._assert_order_status(order, [OrderStatus.PENDING, OrderStatus.ACCEPTED])

        total_profit = 0

        for item in order.items.all():
            product = item.product
            if product.stock < item.amount:
                raise ValidationError(
                    f"{product.name} mahsuloti yetarli emas. Zaxira: {product.stock}, So‘rov: {item.amount}")

        for item in order.items.all():
            total_profit += item.product.decrease_stock(item.amount)

        order.status = OrderStatus.COMPLETED
        order.usd_exchange_rate = order.shop.usd_exchange_rate
        order.admin = admin
        order.profit = total_profit
        order.save()

        self._create_notification(order.customer, order.shop, NotificationType.ORDER_EVENT_USER, order)

        return order

    def accept_order(self, order: Order, admin: User):
        self._assert_order_status(order, [OrderStatus.PENDING])

        order.status = OrderStatus.ACCEPTED
        order.admin = admin
        order.usd_exchange_rate = order.shop.usd_exchange_rate
        order.save()

        self._create_notification(order.customer, order.shop, NotificationType.ORDER_EVENT_USER, order)

        return True
