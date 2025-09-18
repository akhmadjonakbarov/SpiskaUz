from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ("pk", "shop", "date", "amount", "transaction_type", "created_at")
    list_filter = ("transaction_type", "date")
    search_fields = ("description",)
