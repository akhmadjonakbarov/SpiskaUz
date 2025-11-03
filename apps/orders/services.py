from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.cart.models import Cart, CartItem
from apps.notifications.models import Notification, NotificationType
from apps.users.models import User
from .models import Order, OrderItem, OrderPaymentMethod, OrderStatus, ProductOrderItemInfo
from ..currency_rate.models import CurrencyRate
from apps.document.models import Document, PaymentDetail, DocumentItem, DocumentItemBalance, DocumentOrder


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

    def restore_order(self, user: User, order: Order) -> Cart:
        cart, _ = Cart.objects.get_or_create(customer=user, shop=order.shop)
        for order_item in order.items.all():
            CartItem.objects.create(
                cart=cart, product=order_item.product, amount=order_item.amount
            )

        return cart

    def complete_order(self, order: Order):
        self._assert_order_status(order, [OrderStatus.PENDING, OrderStatus.ACCEPTED])
        order.status = OrderStatus.COMPLETED
        order.save()
        self._create_notification(order.customer, order.shop, NotificationType.ORDER_EVENT_USER, order)

        return order

    def accept_order(self, order: Order, admin: User):
        try:
            self._assert_order_status(order, [OrderStatus.PENDING])
            document = Document.objects.create(
                doc_type='sell', user=admin, shop=order.shop
            )
            PaymentDetail.objects.create(
                payment_method=order.payment_detail.payment_method, document=document,
                discount=order.discount if order.discount is not None else Decimal('0.0'),
                promo_code_value=Decimal('0.0')
            )
            latest_currency = CurrencyRate.objects.filter(
                shop=document.shop
            ).order_by('-created_at').first()

            for oi in order.items.all():
                order_item: OrderItem = oi
                sell_qty = Decimal(str(order_item.amount))
                balances = DocumentItemBalance.objects.filter(
                    product=order_item.product,
                    shop=document.shop,
                    qty__gt=0
                ).order_by('created_at')

                total_available = sum(b.qty for b in balances)
                if Decimal(total_available) < sell_qty:
                    raise Exception(f"Not enough stock for product {order_item.product.name}.")
                remaining_qty = sell_qty
                for balance in balances:
                    if remaining_qty <= 0:
                        break

                    deduct_qty = min(balance.qty, remaining_qty)

                    DocumentItem.objects.create(
                        document=document,
                        product=order_item.product,
                        currency_rate=latest_currency if order_item.product.currency_type == 'usd' else None,
                        currency_rate_value=latest_currency.rate if order_item.product.currency_type == 'usd' else Decimal(
                            '0.0'),
                        qty=deduct_qty,
                        income_price=balance.income_price,
                        sale_price=balance.sale_price,
                        profit_as_percent=balance.profit_as_percent,
                        shop=document.shop,
                        user=document.user,

                    )

                    balance.qty -= deduct_qty
                    balance.save()

                    remaining_qty -= deduct_qty

            order.status = OrderStatus.ACCEPTED
            order.admin = admin
            order.save()

            DocumentOrder.objects.create(
                order=order, document=document
            )

            self._create_notification(order.customer, order.shop, NotificationType.ORDER_EVENT_USER, order)

            return True
        except Exception as e:
            raise e
