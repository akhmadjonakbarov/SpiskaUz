from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from import_export.admin import ExportActionModelAdmin
from unfold.admin import ModelAdmin

from .models import Advertisement, AdvertisementCategory


@admin.register(AdvertisementCategory)
class AdvertisementCategoryAdmin(ModelAdmin, GuardedModelAdmin, ExportActionModelAdmin):
    list_display = ["name"]


@admin.register(Advertisement)
class AdvertisementAdmin(ModelAdmin, GuardedModelAdmin):
    list_display = ["name", "description", "category", "price", "phone", "shop", "owner", "status", "published", "address", "latitude", "longitude", "created_at"]
    list_horizontal_scrollbar_top = True
