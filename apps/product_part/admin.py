from django.contrib import admin
from .models import ProductPart
from unfold.admin import ModelAdmin


# Register your models here.
@admin.register(ProductPart)
class ProductPartAdmin(ModelAdmin):
    list_display = ('id', 'product', 'sale_price', 'income_price', 'qty', 'confirmed_by', 'is_confirm',
                    'profit_as_percent',)

    def sale_price(self, product_part: ProductPart):
        return product_part.product.sale_price
