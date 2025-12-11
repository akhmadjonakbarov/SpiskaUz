from django.db import models
from django.utils import timezone

from apps.base.models import BaseModel
from apps.role_manager.models import Role


class SalaryTransaction(BaseModel):
    user_role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        "users.User", blank=True, null=True, on_delete=models.SET_NULL,
        related_name="creator"
    )
    is_active = models.BooleanField(default=True, blank=True, null=True)

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user_role} - {self.amount} on {self.date_paid}"
