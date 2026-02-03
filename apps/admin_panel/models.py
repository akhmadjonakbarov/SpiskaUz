from decimal import Decimal
from django.db import models
from apps.base.models import BaseModel


# Create your models here.
class SalaryBalance(BaseModel):
    role = models.OneToOneField(
        "role_manager.Role", on_delete=models.CASCADE,
        verbose_name="Role", related_name="balance_as_salary"
    )
    balance = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name="Balance", default=Decimal("0.0"),
    )
    personal_salary = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name="Personal Salary",
        default=Decimal("0.0"),
        blank=True, null=True,
    )
    global_salary = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name="Global Salary",
        blank=True, null=True,
        default=Decimal("0.0"),
    )

    @property
    def total_salary(self):
        return self.balance + self.global_salary + self.personal_salary

    def __str__(self):
        return f"{self.balance}"




class PercentageTracker(BaseModel):
    document = models.OneToOneField(
        "document.Document", on_delete=models.CASCADE, verbose_name="Document"
    )

    def __str__(self):
        return f"{self.document}"
