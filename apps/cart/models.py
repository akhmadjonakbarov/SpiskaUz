from functools import reduce

from django.db import models

from apps.products.models import Product
from apps.promocodes.models import Promocode
from apps.shops.models import Shop
from apps.users.models import User


class ShoppingCart(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="carts", verbose_name="Shop")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts", verbose_name="User")
    promocode = models.ForeignKey(Promocode, on_delete=models.SET_NULL, null=True, blank=True, related_name="carts")

    def calc_total_price(self):
        return reduce(lambda prev, item: prev + item.amount * item.product.sale_price, self.items.all(), 0)


class ShoppingCartItem(models.Model):
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name="items", verbose_name="Shopping Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"CartItem(product={self.product}, amount={self.amount})"

    def sale_price_with_discount(self):
        promocode = getattr(self.cart, "promocode", None)

        item = None

        if promocode:
            items = getattr(promocode, "_prefetched_objects_cache", {}).get("items")

            if items is not None:
                item = next((i for i in items if i.product_id == self.product_id), None)

            else:
                item = promocode.items.filter(product_id=self.product).first()

        return self.product.sale_price - item.discount if item else self.product.sale_price
