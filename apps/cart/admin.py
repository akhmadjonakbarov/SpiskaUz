from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import ShoppingCart, ShoppingCartItem


class ShoppingCartItemInline(TabularInline):
    model = ShoppingCartItem
    extra = 1


@admin.register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ["pk", "shop", "user", "promocode"]
    inlines = [ShoppingCartItemInline]
    min_num = 1
