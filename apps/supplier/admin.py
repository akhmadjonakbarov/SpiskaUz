from django.contrib import admin

from .models import SupplierDebtBalance, Supplier, Transaction
from ..base.admin import BaseAdmin


@admin.register(Supplier)
class SupplierAdmin(BaseAdmin):
    list_display = ('id','name', 'phone_number')


@admin.register(SupplierDebtBalance)
class SupplierDebtBalanceAdmin(BaseAdmin):
    list_display = ('supplier', 'balance_usd', 'balance_uzs')


@admin.register(Transaction)
class DebtPaymentHistoryAdmin(BaseAdmin):
    list_display = (
        'amount', 'currency_type', 'created_by', 'balance',
    )
