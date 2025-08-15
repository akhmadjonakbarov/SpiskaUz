from django.db import models

from apps.base.models import BaseModelWithUser


# Create your models here.
class Client(BaseModelWithUser):
    full_name = models.CharField(max_length=250)
    phone_number1 = models.CharField(max_length=9)
    phone_number2 = models.CharField(max_length=9, blank=True, null=True)
    address = models.CharField(max_length=250)

    def __str__(self):
        return self.full_name
