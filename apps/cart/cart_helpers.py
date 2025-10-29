from decimal import Decimal


class CartHelpers:

    @staticmethod
    def get_total_price(cart):
        from apps.cart.models import Cart, CartItem
        from utils.convertor import Convertor
        from apps.document.models import DocumentItemBalance
        from apps.currency_rate.models import CurrencyRate
        total_price = Decimal('0.0')

        for item in cart.items.all():
            cart_item: CartItem = item
            balance = DocumentItemBalance.objects.filter(
                product=cart_item.product, shop=cart.shop
            ).first()
            if balance is not None:
                if cart_item.product.currency_type.lower() in 'usd':
                    converted_price = Convertor.to_decimal(balance.sale_price) * Convertor.to_decimal(
                        balance.currency_rate_value)
                    total_price = total_price + converted_price * Convertor.to_decimal(cart_item.amount)
                else:
                    total_price = total_price + Convertor.to_decimal(balance.sale_price) * Convertor.to_decimal(
                        cart_item.amount)
            else:
                latest = CurrencyRate.objects.order_by('-created_at').filter(
                    shop=cart_item.cart.shop
                ).first()
                if cart_item.product.currency_type.lower() in 'usd':
                    converted_price = Convertor.to_decimal(cart_item.product.sale_price) * Convertor.to_decimal(
                        latest.rate)
                    total_price = total_price + converted_price * Convertor.to_decimal(cart_item.amount)
                else:
                    total_price = total_price + Convertor.to_decimal(
                        cart_item.product.sale_price) * Convertor.to_decimal(
                        cart_item.amount)
        return total_price
