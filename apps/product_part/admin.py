from django.contrib import admin
from .models import ProductPart


# Register your models here.
@admin.register(ProductPart)
class ProductPartAdmin(admin.ModelAdmin):
    pass
