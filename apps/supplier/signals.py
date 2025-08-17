from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Supplier, SupplierDebtBalance


@receiver(post_save, sender=Supplier)
def create_supplier_balance(sender, instance, created, **kwargs):
    if created:
        SupplierDebtBalance.objects.create(supplier=instance)
