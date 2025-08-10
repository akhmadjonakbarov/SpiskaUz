from django.contrib import admin

from .models import RoleUser
from ..base.admin import BaseAdmin


@admin.register(RoleUser)
class RoleUserAdmin(BaseAdmin):
    list_display = ('user', 'role', 'shop', 'created_by')
