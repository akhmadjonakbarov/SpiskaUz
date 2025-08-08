from django.contrib import admin
from .models import Unit


# Register your models here.
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    pass
