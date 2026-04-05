from django.contrib import admin

# Register your models here.
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Season, SeasonItem, GameUserBalance, GameItem


# --- Inlines ---

class SeasonItemInline(TabularInline):
    model = SeasonItem
    extra = 1
    fields = ["price"]


class GameItemInline(TabularInline):
    model = GameItem
    extra = 0
    readonly_fields = ["season_item", "created_at"]
    can_delete = False
    verbose_name = "Prize History"
    verbose_name_plural = "Prize History"


# --- Admin Classes ---

@admin.register(Season)
class SeasonAdmin(ModelAdmin):
    list_display = ["id", "name", "shop", "user", "created_at"]
    list_filter = ["shop", "user"]
    search_fields = ["name", "shop__name"]
    inlines = [SeasonItemInline]


@admin.register(SeasonItem)
class SeasonItemAdmin(ModelAdmin):
    list_display = ["id", "season", "price", "created_at"]
    list_filter = ["season__shop", "season"]
    search_fields = ["season__name"]


@admin.register(GameUserBalance)
class GameUserBalanceAdmin(ModelAdmin):
    list_display = ["id", "user", "balance", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__get_full_name", "user__phone"]
    # Prevent manual balance manipulation for safety
    readonly_fields = ["balance"]
    inlines = [GameItemInline]


@admin.register(GameItem)
class GameItemAdmin(ModelAdmin):
    list_display = ["id", "game_balance", "season_item", "created_at"]
    list_filter = ["season_item__season", "created_at"]
    list_display_links = ["id", "game_balance"]
