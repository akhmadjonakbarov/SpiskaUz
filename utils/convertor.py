from decimal import Decimal, InvalidOperation


class Convertor:
    @staticmethod
    def to_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0.0")
        try:
            return Decimal(str(value))
        except (ValueError, InvalidOperation):
            raise ValueError(f"Cannot convert {value} to Decimal.")

    @staticmethod
    def to_float(value) -> float:
        if value is None:
            return 0.0
        try:
            return float(round(value, 5))
        except (ValueError, InvalidOperation):
            raise ValueError(f"Cannot convert {value} to Float.")
