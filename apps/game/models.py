from django.db import models

from apps.base.models import BaseModelWithUser, BaseModelWithUserAndShop, BaseModel


class Season(BaseModelWithUserAndShop):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class SeasonItem(BaseModel):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="items")
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.price)


class GameUserBalance(BaseModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)


class GameItem(BaseModel):
    game_balance = models.ForeignKey(GameUserBalance, on_delete=models.CASCADE)
    season_item = models.ForeignKey(SeasonItem, on_delete=models.CASCADE)
