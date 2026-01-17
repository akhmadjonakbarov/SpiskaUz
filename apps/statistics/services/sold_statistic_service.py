from decimal import Decimal
from django.db.models import F, Sum
from utils.convertor import Convertor
from apps.document.models import DocumentItem
from apps.debt.models import Debt


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
        return self.get_total_price() - self.get_total_income_price()

    def get_total_discount(self) -> Decimal:
        discount = (
                self.documents
                .aggregate(total=Sum("payment_detail__discount"))
                .get("total")
                or Decimal("0.0")
        )
        return Convertor.to_decimal(discount)

    def get_total_debt(self) -> Decimal:
        debts = Debt.actives.filter(
            shop=self.shop,
            is_paid=False,
            document__in=self.documents
        ).select_related("document")

        total = Decimal("0.0")
        paid = Decimal("0.0")

        for debt in debts:
            paid += Convertor.to_decimal(debt.paid_money)

            items = debt.document.document_items.filter(deleted_at=None).select_related("product")
            for item in items:
                price = item.qty * item.sale_price
                if item.product.currency_type.lower() == "usd":
                    price *= item.currency_rate_value
                total += Convertor.to_decimal(price)

        return total - paid

    def get_agreed_price(self) -> Decimal:
        total_price = self.get_total_price()
        discount = self.get_total_discount()
        return total_price - discount

    def calculate(self) -> dict:
        return {
            "total_price": self.get_total_price(),
            "discount": self.get_total_discount(),
            "agreed_price": self.get_agreed_price(),
            "amount_cash": Decimal("0.0"),
            "debt": self.get_total_debt(),
            "total_profit": self.get_total_profit(),
        }
