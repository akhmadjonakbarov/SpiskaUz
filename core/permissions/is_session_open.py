from rest_framework.permissions import BasePermission
from django.utils import timezone
from apps.daily_session.models import DailySession
from apps.shops.models import Shop


class IsSessionOpen(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        # Try to get shop_id from URL kwargs or request body
        shop_id = view.kwargs.get('shop_id') or request.data.get('shop_id') or request.query_params.get('shop_id')

        if not shop_id:
            return False  # No shop specified

        try:
            shop = Shop.objects.get(id=shop_id, users=user)  # assuming ManyToManyField or related check
        except Shop.DoesNotExist:
            return False  # Not user's shop or invalid shop

        today = timezone.now().date()
        session = DailySession.objects.filter(
            shop=shop,
            date=today,
            is_open=True
        ).first()

        return session is not None
