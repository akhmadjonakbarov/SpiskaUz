from decimal import Decimal

from apps.statistics.services.debt_calculator import SupplierDebtCalculatorService
from apps.statistics.services.shop_balance_calculator import ShopBalanceCalculatorService
from utils.convertor import Convertor


class BoughtStatisticService:
    def __init__(self, shop, documents):
        self.shop = shop
        self.documents = documents

    def get_total_price(self) -> Decimal:
        total = Decimal("0.0")

        for doc in self.documents:
            for item in doc.document_items.all():
                price = item.qty * item.income_price
                if item.product.currency_type.lower() == "usd":
                    price *= item.currency_rate_value

                total += Convertor.to_decimal(price)

        return total

    def calculate(self, from_date=None, to_date=None) -> dict:
        return {
            "total_price": self.get_total_price(),
            "total_debt": SupplierDebtCalculatorService(self.shop).calculate(from_date, to_date),
            "removed_profit": ShopBalanceCalculatorService.calculate_removed_price(
                self.shop, "loss", from_date, to_date
            ),
            "removed_cash": ShopBalanceCalculatorService.calculate_removed_price(
                self.shop, "cash_loss", from_date, to_date
            ),
        }