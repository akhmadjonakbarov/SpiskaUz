from decimal import Decimal
from django.db.models import Sum
from apps.shops.models import ShopBalanceTransaction
from utils.convertor import Convertor


class ShopBalanceCalculatorService:
    @staticmethod
    def calculate_removed_price(shop, kind, from_date=None, to_date=None):
        query = ShopBalanceTransaction.actives.filter(shop=shop, kind=kind)
        if from_date:
            query = query.filter(created_at__gte=from_date)
        if to_date:
            query = query.filter(created_at__lt=to_date)

        result = query.aggregate(total=Sum("amount"))
        total = result["total"] or Decimal("0.0")
        return Convertor.to_decimal(total)
