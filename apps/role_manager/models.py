from django.db import models

from apps.base.models import BaseModel
from apps.users.models import User


class Role(BaseModel):
    ROLES = (
        ('cashier_admin', 'CASHIER_ADMIN'),
        ('owner', 'OWNER'),
        ('main_admin', 'MAIN_ADMIN')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="roles"
    )
    salary = models.DecimalField(
        max_digits=30, decimal_places=5, blank=True, null=True
    )
    role = models.CharField(
        choices=ROLES, max_length=20
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    total_approved_orders_commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Total Approved Orders Commission (%)",
        blank=True, null=True
    )
    admin_approved_orders_commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="Admin Approved Orders Commission (%)",
        blank=True, null=True
    )

    def __str__(self):
        return f"{self.role} - {self.user}"
