from django.contrib import admin
from .models import DailySession
from ..base.admin import BaseAdmin


@admin.register(DailySession)
class DailySessionAdmin(BaseAdmin):
    pass
