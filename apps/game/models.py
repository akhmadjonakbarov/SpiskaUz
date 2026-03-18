from django.db import models

from apps.base.models import BaseModelWithUserAndShop, BaseModel


class Season(BaseModelWithUserAndShop):
    name = models.CharField(max_length=120)
    limit_price = models.IntegerField(null=True, blank=True)
    end_date = models.DateTimeField(blank=True, null=True)
    has_debt = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class SeasonItem(BaseModel):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="items")
    price = models.IntegerField()

    def __str__(self):
        return str(self.price)


class GameUserBalance(BaseModel):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="user_balance")
    balance = models.DecimalField(max_digits=10, decimal_places=2)


class GameItem(BaseModel):
    game_balance = models.ForeignKey(GameUserBalance, on_delete=models.CASCADE, related_name="balance_items")
    season_item = models.ForeignKey(SeasonItem, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, blank=True, null=True)
