from django.contrib import admin
from unfold.admin import  ModelAdmin

from .models import SalaryTransaction


@admin.register(SalaryTransaction)
class SalaryTransactionAdmin(ModelAdmin):
    list_display = ('user_role', 'amount', 'date_paid', 'description')
    search_fields = ('user_role__user__username', 'description')
    list_filter = ('date_paid',)
