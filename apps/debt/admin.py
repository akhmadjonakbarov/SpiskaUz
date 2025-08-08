from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import DebtConversion, DebtPayment


@admin.register(DebtConversion)
class DebtConversionAdmin(ModelAdmin):
    list_display = ["id", "shop", "user", "amount_uzs", "amount_usd", "converted_at", "reverted"]


@admin.register(DebtPayment)
class DebtPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "shop", "user", "amount", "currency", "paid_at"]
