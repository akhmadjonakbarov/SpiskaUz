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
        pass
