from django.contrib import admin
from .models import DailySession
from apps.base.admin import BaseAdmin


@admin.register(DailySession)
class DailySessionAdmin(BaseAdmin):
    list_display = ('shop', 'is_open', 'date')
