from django.apps import AppConfig


class SupplierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.supplier'

    def ready(self):
        import apps.supplier.signals
