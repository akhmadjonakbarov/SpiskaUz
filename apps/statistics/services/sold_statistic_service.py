from decimal import Decimal
from django.db.models import F, Sum

from apps.shops.models import ShopBalance
from apps.statistics.services.debt_calculator import ShopDebtCalculatorService
from utils.convertor import Convertor
from apps.document.models import DocumentItem


class SoldStatisticService:

    def __init__(self, shop, documents):
        self.shop = shop
        self.documents = documents

    def get_total_price(self) -> Decimal:
        items = DocumentItem.actives.filter(
            document__in=self.documents,
        ).select_related("product")

        total = Decimal("0.0")

        for item in items:
            price = item.qty * item.sale_price
            if item.product.currency_type.lower() == "usd":
                price *= item.currency_rate_value
            total += Convertor.to_decimal(price)

        return total

    def get_total_income_price(self) -> Decimal:
        items = DocumentItem.actives.filter(
            document__in=self.documents,
        ).select_related("product")

        total = Decimal("0.0")

        for item in items:
            price = item.qty * item.income_price
            if item.product.currency_type.lower() == "usd":
                price *= item.currency_rate_value
            total += Convertor.to_decimal(price)

        return total

    def get_total_profit(self) -> Decimal:
        print(f'[+] Sale price: {self.get_total_price()}')
        print(f'[+] Income price: {self.get_total_income_price()}')
        total_profit_from_products = self.get_total_price() - self.get_total_income_price()
        shop_balance:ShopBalance = self.shop.balance
        return shop_balance.profit + total_profit_from_products

    def get_total_discount(self) -> Decimal:
        discount = (
                self.documents
                .aggregate(total=Sum("payment_detail__discount"))
                .get("total")
                or Decimal("0.0")
        )
        return Convertor.to_decimal(discount)

    def get_total_debt(self) -> Decimal:
        return ShopDebtCalculatorService(self.shop).calculate()

    def get_agreed_price(self) -> Decimal:
        total_price = self.get_total_price()
        discount = self.get_total_discount()
        return total_price - discount

    def get_amount_cash(self) -> Decimal:
        shop_balance:ShopBalance = self.shop.balance
        total_price = shop_balance.cash
        return total_price

    def calculate(self) -> dict:
        return {
            "total_price": self.get_total_price(),
            "discount": self.get_total_discount(),
            "agreed_price": self.get_agreed_price(),
            "amount_cash": self.get_amount_cash(),
            "debt": self.get_total_debt(),
            "total_profit": self.get_total_profit(),
        }
