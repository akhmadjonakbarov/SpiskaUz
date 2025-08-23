from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from unfold.admin import ModelAdmin, TabularInline

from .models import Admin as ShopAdminModel, Shop, ShopCategory, ShopBalance, ShopBalanceTransaction


class ShopCategoryInline(TabularInline):
    model = ShopCategory
    extra = 1


class ShopAdminInline(TabularInline):
    model = ShopAdminModel
    extra = 0


@admin.register(Shop)
class ShopAdmin(ModelAdmin, GuardedModelAdmin):
    list_display = ["pk", "short_name", "owner", "latitude", "longitude", "created_at"]
    list_filter = ["owner"]
    search_fields = ["name", "owner__first_name", "owner__last_name"]
    inlines = [ShopCategoryInline, ShopAdminInline]

    def short_name(self, obj):
        length = 30
        return obj.name[:length] + ("..." if len(obj.name) > length else "")

    short_name.short_description = "Name"


@admin.register(ShopBalance)
class ShopBalanceAdmin(ModelAdmin):
    list_display = ('id','profit', 'cash', 'shop', 'created_by')


@admin.register(ShopBalanceTransaction)
class ShopBalanceTransactionAdmin(ModelAdmin):
    list_display = ('id','value', 'kind', 'shop', 'created_by')
