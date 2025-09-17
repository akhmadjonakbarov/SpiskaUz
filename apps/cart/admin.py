from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem


class ShoppingCartItemInline(TabularInline):
    model = CartItem
    extra = 1


@admin.register(Cart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ["pk", "shop", "customer", "promocode"]
    inlines = [ShoppingCartItemInline]
    min_num = 1
