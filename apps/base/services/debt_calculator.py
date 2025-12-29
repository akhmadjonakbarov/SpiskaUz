from decimal import Decimal


class BaseDebtCalculatorService:
    def __init__(self, shop):
        self.shop = shop

    def calculate(self) -> Decimal:
        raise NotImplementedError

    def _get_currency_rate(self) -> Decimal:
        from apps.currency_rate.models import CurrencyRate
        return (
            CurrencyRate.actives
            .filter(shop=self.shop)
            .order_by("-created_at")
            .first()
        )
