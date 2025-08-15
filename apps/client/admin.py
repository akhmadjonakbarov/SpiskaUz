from django.contrib import admin
from .models import Client
from unfold.admin import ModelAdmin


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    pass
