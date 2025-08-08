from guardian.admin import GuardedModelAdmin
from unfold.admin import ModelAdmin


class BaseAdmin(ModelAdmin):
    pass


class BaseAdminWithGuarded(BaseAdmin, GuardedModelAdmin):
    pass
