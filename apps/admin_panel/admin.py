from django.contrib import admin
from .models import SalaryBalance


@admin.register(SalaryBalance)
class SalaryBalanceAdmin(admin.ModelAdmin):
    list_display = ('id','balance', 'personal_salary', 'global_salary')
