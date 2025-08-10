from django.contrib import admin

from .models import Role
from ..base.admin import BaseAdmin


@admin.register(Role)
class RoleUserAdmin(BaseAdmin):
    list_display = ('user', 'role', 'shop', 'created_by')
