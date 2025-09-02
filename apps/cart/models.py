from functools import reduce

from django.db import models

from apps.base.models import BaseModel
from apps.products.models import Product
from apps.promocodes.models import PromoCode
from apps.shops.models import Shop
from apps.users.models import User


class Cart(BaseModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="carts", verbose_name="Shop")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart", verbose_name="User")
    promocode = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name="carts")

    def calc_total_price(self):
        return reduce(lambda prev, item: prev + item.amount * item.product.sale_price, self.items.all(), 0)


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"CartItem(product={self.product}, amount={self.amount})"
