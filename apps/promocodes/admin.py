from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from unfold.admin import ModelAdmin, TabularInline

from .models import Promocode, PromocodeItem, PromocodeUsage


class PromocodeItemInline(TabularInline):
    model = PromocodeItem
    extra = 1

    def get_extra(self, request, obj=..., **kwargs):
        if obj is not None:
            return obj.shop.products.count() - obj.items.count()

        return super().get_extra(request, obj, **kwargs)

    def get_max_num(self, request, obj=..., **kwargs):
        if obj is not None:
            return obj.shop.products.count()

        return super().get_max_num(request, obj, **kwargs)


@admin.register(Promocode)
class PromocodeAdmin(ModelAdmin):
    list_display = ["pk", "shop", "code", "value"]
    inlines = [PromocodeItemInline]

    def active(self, obj):
        return obj.is_active

    active.boolean = True


@admin.register(PromocodeUsage)
class PromocodeUsageAdmin(GuardedModelAdmin):
    list_display = ["pk", "promocode", "user", "used_at"]
    list_filter = ["promocode", "user"]
    search_fields = ["promocode__code", "user__username"]
