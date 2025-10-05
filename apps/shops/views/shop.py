from decimal import Decimal

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.shops.models import Shop, Category, ShopBalance

from apps.shops.serializers import ShopSerializer, ShopDetailSerializer
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

    queryset = Shop.objects.prefetch_related(
        "categories",
        "contacts",
        "products",
        "members"
    ).filter(deleted_at=None).all().order_by("created_at")
    serializer_class = ShopSerializer
    parser_classes = [FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

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
        shop = serializer.save()
        shop.members.add(self.request.user)

        Role.objects.create(
            user=self.request.user,
            role='owner', shop=shop, created_by=self.request.user,
        )
        ShopBalance.objects.create(
            shop=shop,
            created_by=self.request.user,
            profit=Decimal('0.0'),
            cash=Decimal('0.0')
        )

        category = Category.objects.filter(name="Umumiy", shops=shop).first()
        if category is None:
            category = Category.objects.create(
                user=self.request.user,
                can_delete=False,
                name="Umumiy"
            )
            category.shops.add(shop)
            category.save()

        # Create CurrencyRate entry
        CurrencyRate.objects.create(
            user=self.request.user,
            shop=shop,
            rate=usd_exchange_rate,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ShopDetailSerializer(instance, many=False, context={"request": request})
        return Response(serializer.data)
