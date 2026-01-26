from decimal import Decimal

from django.db.models import Sum

from apps.base.services.debt_calculator import BaseDebtCalculatorService


class SupplierDebtCalculatorService(BaseDebtCalculatorService):
    def calculate(self, from_date=None, to_date=None) -> Decimal:
        total = Decimal("0.0")
        currency = self._get_currency_rate()

        suppliers = (
            self.shop.suppliers
            .select_related("debt_balance")
            .all()
        )

        if from_date:
            suppliers = suppliers.filter(created_at__gte=from_date)
        if to_date:
            suppliers = suppliers.filter(created_at__lt=to_date)

        for supplier in suppliers:
            balance = supplier.debt_balance
            total += balance.balance_uzs

            if balance.balance_usd > 0 and currency:
                total += balance.balance_usd * currency.rate

        return total


class CustomerDebtCalculatorService(BaseDebtCalculatorService):
    def calculate(self) -> Decimal:
        pass


class ShopDebtCalculatorService(BaseDebtCalculatorService):
    def calculate(self) -> Decimal:
        orders = self.shop.orders.all()
        total = Decimal("0.0")
        for order in orders:
            total_debt = order.transactions.filter(
                transaction_type="debt"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0

            difference_of_debt = order.payment_detail.un_payed - total_debt
            if difference_of_debt > 0:
                total += difference_of_debt

        return total
