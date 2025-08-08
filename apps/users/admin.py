from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from guardian.admin import GuardedModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin

from .models import OTP, User


@admin.register(User)
class CustomUserAdmin(ModelAdmin, UserAdmin, ImportExportModelAdmin):
    model = User
    list_display = ("id", "first_name", "last_name", "phone", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "phone", "password", "avatar")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
        ("Favorite", {"fields": ("favorite_products", "favorite_advertisements")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("first_name", "last_name", "phone", "password1", "password2", "is_staff", "is_active")}),)
    search_fields = ("phone",)
    ordering = ("phone",)


@admin.register(OTP)
class OTPAdmin(ModelAdmin, ImportExportModelAdmin, GuardedModelAdmin):
    list_display = ("user", "code", "created_at", "is_available")
    search_fields = ("user__phone", "code")
    list_filter = ("created_at",)

    def is_available(self, obj):
        return not obj.is_expired()

    is_available.boolean = True
