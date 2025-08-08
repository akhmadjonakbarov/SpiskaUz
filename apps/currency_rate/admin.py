from django.contrib import admin
from .models import CurrencyRate


# Register your models here.
@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    pass
