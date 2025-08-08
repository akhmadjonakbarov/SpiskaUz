from django.db import models

from apps.base.models import BaseModel


# Create your models here.
class Unit(BaseModel):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name
