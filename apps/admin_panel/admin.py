from django.contrib import admin
from .models import SalaryBalance


@admin.register(SalaryBalance)
class SalaryBalanceAdmin(admin.ModelAdmin):
    pass
