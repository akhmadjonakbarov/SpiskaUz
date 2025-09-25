from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CustomerTransaction


# Register your models here.
@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(ModelAdmin):
    list_display = ('customer', 'order', 'amount', 'currency_rate', 'transaction_type')
