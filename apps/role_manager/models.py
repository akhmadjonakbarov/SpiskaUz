from django.db import models

from apps.base.models import BaseModel
from apps.users.models import User


class Role(BaseModel):
    ROLES = (
        ('cashier_admin', 'CASHIER_ADMIN'),
        ('owner', 'OWNER'),
        ('main_admin', 'MAIN_ADMIN')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user")
    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE,
    )
    salary = models.DecimalField(
        max_digits=30, decimal_places=5, blank=True, null=True
    )
    role = models.CharField(
        choices=ROLES, max_length=20, unique=True
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_by")

    def __str__(self):
        return f"{self.role} - {self.user}"
