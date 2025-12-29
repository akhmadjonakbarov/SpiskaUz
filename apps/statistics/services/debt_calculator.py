from decimal import Decimal

from apps.base.services.debt_calculator import BaseDebtCalculatorService


class SupplierDebtCalculatorService(BaseDebtCalculatorService):
    def calculate(self) -> Decimal:
        total = Decimal("0.0")
        currency = self._get_currency_rate()

        suppliers = (
            self.shop.suppliers
            .select_related("debt_balance")
            .all()
        )

        for supplier in suppliers:
            balance = supplier.debt_balance
            total += balance.balance_uzs

            if balance.balance_usd > 0 and currency:
                total += balance.balance_usd * currency.rate

        return total


class CustomerDebtCalculatorService(BaseDebtCalculatorService):
    def calculate(self) -> Decimal:
        pass
