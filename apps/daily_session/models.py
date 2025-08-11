from django.utils import timezone

from django.db import models

from apps.base.models import BaseModelWithUserAndShop


# Create your models here.
class DailySession(BaseModelWithUserAndShop):
    date = models.DateTimeField(default=timezone.now)
    is_open = models.BooleanField(default=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    def close(self):
        self.is_open = False
        self.closed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.shop.name} - {self.date} - {'Open' if self.is_open else 'Closed'}"
