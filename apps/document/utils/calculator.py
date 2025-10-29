from utils.convertor import Convertor
from decimal import Decimal, ROUND_HALF_UP


class Calculator:
    @staticmethod
    def percentage(sale_price, income_price) -> Decimal:
        if income_price == 0 or income_price == 0.0:
            return Decimal("0.0")

        # Safe conversion using str()
        sale_price = Decimal(str(sale_price))
        income_price = Decimal(str(income_price))

        result = ((sale_price * Decimal("100")) / income_price) - Decimal("100")
        return result.quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def profit(sale_price, income_price):
        return Decimal(sale_price) - Decimal(income_price)

    @staticmethod
    def profit_in_uzs(sale_price, income_price, currency_rate):
        profit = Calculator.profit(sale_price, income_price)
        return Decimal(profit) * Convertor.to_decimal(currency_rate)
