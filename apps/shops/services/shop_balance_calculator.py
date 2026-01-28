from decimal import Decimal
from django.db.models import Sum
from typing import Iterable

from apps.base.models import TransactionType


class ShopBalanceTransactionCalculatorService:
    def __init__(self, transactions: Iterable):
        """
        transactions: QuerySet[ShopBalanceTransaction]
        """
        self.transactions = transactions
        self.profit = Decimal("0.0")
        self.cash = Decimal("0.0")

    # --------------------------------------------------
    # Generic helpers
    # --------------------------------------------------

    def _sum_by_kind(self, kinds: list[str], ) -> Decimal:
        qs = self.transactions.filter(kind__in=kinds)

        value = qs.aggregate(total=Sum("amount"))["total"]
        return value or Decimal("0.0")

    # --------------------------------------------------
    # INCOME / PROFIT
    # --------------------------------------------------

    def get_total_income(self) -> Decimal:
        """
        Pure profit (without cash meaning)
        """
        return self._sum_by_kind([
            TransactionType.PROFIT,
            TransactionType.CASH_PROFIT,
        ])

    def get_total_loss(self) -> Decimal:
        return self._sum_by_kind([
            TransactionType.LOSS,
            TransactionType.CASH_LOSS,
        ])

    def get_net_profit(self) -> Decimal:
        """
        Final profit after losses
        """
        return self.get_total_income() - self.get_total_loss()

    # --------------------------------------------------
    # CASH
    # --------------------------------------------------

    def get_total_cash_income(self) -> Decimal:
        return self._sum_by_kind([
            TransactionType.CASH_INCOME,
            TransactionType.CASH_PROFIT,
        ])

    def get_total_cash_outcome(self) -> Decimal:
        return self._sum_by_kind([
            TransactionType.CASH_OUTCOME,
            TransactionType.CASH_LOSS,
        ])

    def get_total_cash_losses(self, ) -> Decimal:
        return self._sum_by_kind(
            [
                TransactionType.CASH_LOSS,
            ],

        )

    def get_total_profit_losses(self) -> Decimal:
        return self._sum_by_kind(
            [
                TransactionType.LOSS,
            ],
        )

    def get_total_cash(self) -> Decimal:
        """
        Final cash balance
        """
        return self.get_total_cash_income() - self.get_total_cash_outcome()

    # --------------------------------------------------
    # FULL RESULT
    # --------------------------------------------------

    def calculate(self) -> dict:
        """
        Single entry point
        """
        return {
            "profit": self.get_net_profit(),
            "cash": self.get_total_cash(),
            "income": self.get_total_income(),
            "loss": self.get_total_loss(),
            "cash_income": self.get_total_cash_income(),
            "cash_outcome": self.get_total_cash_outcome(),
        }

    def calculate_final_result(self) -> dict:
        for transaction in self.transactions:
            self._apply_transaction(transaction)

        return {
            "profit": self.profit,
            "cash": self.cash,
        }

    # --------------------------------------------------

    def _apply_transaction(self, tx):
        amount = tx.amount
        kind = tx.kind

        if kind == "profit":
            self.profit += amount

        elif kind == "cash_income":
            self.cash += amount

        elif kind == "cash_profit":
            self.profit += amount
            self.cash += amount

        elif kind == "loss":
            self.profit -= amount

        elif kind == "cash_outcome":
            self.cash -= amount

        elif kind == "cash_loss":
            self.cash -= amount
            self.profit -= amount

        else:
            raise ValueError(f"Unknown transaction type: {kind}")
