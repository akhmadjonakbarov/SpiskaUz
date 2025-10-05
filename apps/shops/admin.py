from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from unfold.admin import ModelAdmin, TabularInline

from .models import Admin as ShopAdminModel, Shop, Category, ShopBalance, ShopBalanceTransaction


class ShopAdminInline(TabularInline):
    model = ShopAdminModel
    extra = 0


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Shop)
class ShopAdmin(ModelAdmin, GuardedModelAdmin):
    list_display = ["pk", "short_name",  "latitude", "longitude", "created_at"]
    inlines = [ShopAdminInline]

    def short_name(self, obj):
        length = 30
        return obj.name[:length] + ("..." if len(obj.name) > length else "")

    short_name.short_description = "Name"


@admin.register(ShopBalance)
class ShopBalanceAdmin(ModelAdmin):
    list_display = ('id', 'profit', 'cash', 'shop', 'created_by')


@admin.register(ShopBalanceTransaction)
class ShopBalanceTransactionAdmin(ModelAdmin):
    list_display = ('id', 'amount', 'kind', 'shop', 'created_by')
