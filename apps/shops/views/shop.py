from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.shops.models import Shop, ShopCategory

from apps.shops.serializers import ShopSerializer
from common.mixins import ActionPermissionMixin
from common.paginations import PageSizePagination

from .mixins import (
    AdminActionsMixin,
    ContactActionsMixin,
    ExchangeRateActionsMixin,
    OrderActionMixin,
    ProductActionsMixin,
    ProductGroupActionMixin,
    PromocodeActionsMixin,
    ShopHistoryActionsMixin,
    ShoppingCartActionMixin,
    SubscriptionActionMixin,
    ShopBalanceMixin,
)
from apps.currency_rate.models import CurrencyRate
from apps.role_manager.models import Role


class ShopViewSet(
    OrderActionMixin,
    ActionPermissionMixin,
    SubscriptionActionMixin,
    ProductGroupActionMixin,
    ShoppingCartActionMixin,
    viewsets.ModelViewSet,
    ProductActionsMixin,
    ContactActionsMixin,
    AdminActionsMixin,
    ExchangeRateActionsMixin,
    PromocodeActionsMixin,
    ShopHistoryActionsMixin,
    ShopBalanceMixin,
):
    """
    Do'konlarni boshqarish uchun ViewSet.

    list:
        Barcha do'konlarni olish
    create:
        Yangi do'kon yaratish
    retrieve:
        ID bo'yicha do'konni olish
    update:
        Do'konni to'liq yangilash
    partial_update:
        Do'konni qisman yangilash
    delete:
        Do'konni o'chirish
    join:
        Do'konga qo'shilish
    leave:
        Do'kondan chiqish
    my_subscriptions:
        Foydalanuvchi a'zo bo'lgan do'konlarni olish
    owned:
        Foydalanuvchining do'konlarini olish
    """

    queryset = Shop.objects.select_related("owner").prefetch_related("categories", "contacts", "products",
                                                                     "members").all().order_by("created_at")
    serializer_class = ShopSerializer
    parser_classes = [FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "description", "address", "owner__first_name", "owner__last_name"]
    pagination_class = PageSizePagination

    action_permissions = {
        # ("update_products_order", "merge_products"): [CanEditDeleteShop],
        ("join", "leave", "create"): [IsAuthenticated],
    }

    def perform_create(self, serializer):
        # Pop usd_exchange_rate from the validated data
        usd_exchange_rate = self.request.data.get("usd_exchange_rate")

        if usd_exchange_rate is None:
            raise ValidationError({"usd_exchange_rate": "This field is required."})

        try:
            usd_exchange_rate = float(usd_exchange_rate)
        except ValueError:
            raise ValidationError({"usd_exchange_rate": "Invalid float format."})

        # Save the Shop
        shop = serializer.save(owner=self.request.user)
        shop.members.add(self.request.user)

        Role.objects.create(
            user=self.request.user,
            role='owner', shop=shop, created_by=self.request.user,
        )

        ShopCategory.objects.create(
            user=self.request.user,
            shop=shop, can_delete=False,
            name="Umumiy"
        )

        # Create CurrencyRate entry
        CurrencyRate.objects.create(
            user=self.request.user,
            shop=shop,
            rate=usd_exchange_rate,
        )


class ShopDetailView(DetailView):
    """
    Do'kon haqida batafsil ma'lumot ko'rish uchun View.

    get:
        Link orqali do'kon ma'lumotlarini olish
    """

    template_name = "shop/shop_detail.html"
    queryset = Shop.objects.all()

    def get_object(self, queryset=None):
        return get_object_or_404(Shop, link=self.kwargs["link"])
