from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from unfold.admin import ModelAdmin, TabularInline
from apps.products.models import Category
from .models import Product, ProductGroup, ProductImage, Report, ReportOption
from ..product_part.models import ProductPart


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


class ProductPartInline(TabularInline):
    model = ProductPart
    extra = 1


@admin.register(Category)
class CategoryAdmin(ModelAdmin, GuardedModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(ModelAdmin, GuardedModelAdmin):
    list_display = [
        "id", "name", "sale_price", "currency_type", "barcode", "discount", "group", "category", "shop", "unit",
        "position_number", "is_selected"
    ]
    inlines = [ProductImageInline, ProductPartInline]
    list_filter = ["shop"]

    # def short_name(self, obj):
    #     length = 30
    #     return obj.full_name[:length] + ("..." if len(obj.full_name) > length else "")

    # short_name.short_description = "Name"


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ["pk", "shop", "position"]
    list_filter = ["shop"]
    search_fields = ["shop__name"]


@admin.register(ReportOption)
class ReportOptionAdmin(ModelAdmin):
    list_display = ["id", "parent", "title", "description"]
    list_display_links = ["id", "title"]


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    list_display = ["id", "report_option", "user", "comment"]
    list_display_links = ["id", "report_option", "user", "comment"]
    list_filter = ["report_option", "user", "product"]
