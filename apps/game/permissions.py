from decimal import Decimal

from rest_framework import permissions

from apps.game.models import Season
from apps.orders.models import OrderPaymentDetail
from apps.role_manager.models import Role


class IsEligibleCustomer(permissions.BasePermission):
    """
    Allows access only to users with no debt and purchases over $200.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True

        shop_id = request.query_params.get("shop_id")
        has_no_debt = False

        role = Role.objects.filter(user=user, shop_id=shop_id).first()

        if role is not None:
            return True

        orders = user.customer_orders.filter(shop_id=shop_id)
        total = Decimal('0.0')
        latest_season: Season = Season.objects.order_by('-created_at').filter(shop_id=shop_id).first()
        if latest_season is None:
            return False

        for order in orders:
            payment_detail: OrderPaymentDetail = order.payment_detail
            total += payment_detail.payed

        high_spender = total >= latest_season.limit_price
        return high_spender
