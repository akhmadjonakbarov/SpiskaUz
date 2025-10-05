import uuid
from django.db import models
from django.db.models import Sum
from apps.base.models import BaseModel, BaseModelWithUser, TransactionType
from apps.orders.models import OrderStatus
from apps.users.models import User
from common.utils import generate_unique_text


class Shop(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Name", max_length=256)
    description = models.TextField("Description", max_length=1000)
    link = models.CharField("Link", max_length=32, default=generate_unique_text, unique=True)
    image = models.ImageField("Image", upload_to="shop-images/%Y/")
    members = models.ManyToManyField(User, blank=True, related_name="subscriptions", verbose_name="Members")
    address = models.TextField("Address")
    latitude = models.CharField("Latitude", max_length=200)
    longitude = models.CharField("Longitude", max_length=200)
    telegram_link = models.CharField("Telegram link", max_length=256, null=True, blank=True)

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"
        permissions = [
            ("add_product", "Add product"),
            ("change_product", "Update product"),
            ("delete_product", "Delete product"),
            ("add_category", "Add category"),
            ("change_category", "Update category"),
            ("delete_category", "Delete category"),
            ("confirm_order", "Confirm order"),
            ("cancel_order", "Cancel order"),
        ]

    def __str__(self):
        return self.name

    @property
    def profit(self):
        return self.orders.filter(status=OrderStatus.COMPLETED).aggregate(total=Sum("profit"))["total"] or 0


class Category(BaseModelWithUser):
    name = models.CharField("Name", max_length=256)
    shops = models.ManyToManyField(
        Shop,
        related_name="categories",
        verbose_name="Shops",
        blank=True,
    )
    image = models.ImageField("Image", upload_to="shop-category-images/",
                              default="shop-category-images/default-image.png")
    can_delete = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class ShopContact(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="contacts")
    full_name = models.CharField("Full name", max_length=256)
    phone_number = models.CharField("Phone number", max_length=20)

    class Meta:
        unique_together = ["shop", "phone_number"]


class Admin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name="Shop", related_name="admins")

    type = models.CharField("Admin Type", choices=(("chief admin", "Chief admin"), ("cash admin", "Cash admin")),
                            max_length=64)
    monthly_salary = models.DecimalField("Salary", max_digits=14, decimal_places=2)

    total_approved_orders_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                                                      verbose_name="Total Approved Orders Commission (%)")
    admin_approved_orders_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                                                      verbose_name="Admin Approved Orders Commission (%)")

    class Meta:
        unique_together = [
            "user", "shop"
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.shop.name}"


class ShopBalance(BaseModel):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shop_balances")
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name="balance")
    profit = models.DecimalField(
        max_digits=50, decimal_places=5,
    )
    cash = models.DecimalField(
        max_digits=50, decimal_places=5
    )

    def __str__(self):
        return f'Cash: {self.cash} Profit: {self.profit}'


class ShopBalanceTransaction(BaseModel):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_balance_transactions")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="shop_balance_transactions")
    balance = models.ForeignKey(
        ShopBalance, related_name="transactions", on_delete=models.SET_NULL, blank=True,
        null=True
    )
    kind = models.CharField(
        choices=TransactionType.choices, max_length=20
    )
    amount = models.DecimalField(
        max_digits=50, decimal_places=5
    )
    note = models.CharField(max_length=400, blank=True, null=True)

    def __str__(self):
        return f'Value: {self.amount} Type: {self.kind}'
