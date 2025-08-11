from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.cart.models import ShoppingCart
from apps.notifications.models import NotificationType
from apps.shops.models import Shop, ShopCategory, ShopContact
from apps.users.serializers import UserSerializer

from .models import Admin
from ..role_manager.models import Role


class ShopCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopCategory
        fields = ["id", "name", "shop", "image", "can_delete"]

        read_only_fields = ["can_delete"]


class ShopContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopContact
        fields = ["id", "shop", "full_name", "phone_number"]
        extra_kwargs = {
            "shop": {"write_only": True},
        }

        validators = [
            UniqueTogetherValidator(ShopContact.objects.all(), fields=["shop", "phone_number"],
                                    message="Do'konga bunday telefon raqam allaqachon qo'shilgan"),
        ]


class ShopSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    share_link = serializers.SerializerMethodField()
    categories = ShopCategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    contacts = ShopContactSerializer(many=True, read_only=True)
    is_member = serializers.SerializerMethodField()
    has_notifications = serializers.SerializerMethodField()
    has_cart_item = serializers.SerializerMethodField()
    usd_exchange_rate = serializers.FloatField(write_only=True)  # or read_only=True if it's output only
    currency = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "owner",
            "description",
            "image",
            "usd_exchange_rate",
            "address",
            "latitude",
            "longitude",
            "created_at",
            "share_link",
            "categories",
            "product_count",
            "contacts",
            "telegram_link",
            "is_member",
            "has_notifications",
            "has_cart_item",
            "currency",
            "role",
            "is_open"
        ]

    def create(self, validated_data):
        # Remove the non-model field manually
        validated_data.pop('usd_exchange_rate', None)
        return super().create(validated_data)

    def get_is_open(self, obj):
        from apps.daily_session.models import DailySession
        today = timezone.now()
        session = DailySession.objects.filter(
            shop=obj, date__day=today.day, date__year=today.year, date__month=today.month
        ).first()
        print(session)

        if session is None:
            return False
        if session.is_open:
            return True
        else:
            return False

    def get_has_notifications(self, shop: Shop):
        user = self.context["request"].user
        return shop.notifications.filter(user=user).exists()

    def get_share_link(self, obj):
        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                reverse("shop_detail", args=[str(obj.id)])
            )

        return f"http://127.0.0.1:8000/api/v1/shop/{obj.id}/"

    def get_currency(self, shop: Shop):
        from apps.currency_rate.models import CurrencyRate
        from apps.currency_rate.serializers import CurrencyRateSerializer

        currency = CurrencyRate.objects.filter(
            shop=shop, deleted_at=None
        ).order_by('-created_at').first()  # Get the most recently created

        if currency:
            return CurrencyRateSerializer(currency).data

        return None  # or {} if you prefer an empty dict

    def get_product_count(self, obj: Shop):
        return obj.products.all().count()

    def get_is_member(self, obj: Shop):
        request = self.context.get("request")

        user = request.user if request and hasattr(request, "user") else None

        if user:
            return user in obj.members.all()

        return False

    def get_role(self, obj):
        from apps.role_manager.serializer import RoleSerializer
        request = self.context.get("request")

        role = Role.objects.filter(
            user=request.user, shop=obj
        ).first()
        return RoleSerializer(role, many=False).data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["owner"] = UserSerializer(instance.owner, context={"request": self.context.get("request")}).data

        return data

    def get_has_cart_item(self, instance):
        user = self.context["request"].user
        cart, _ = ShoppingCart.objects.get_or_create(user=user, shop=instance)

        return cart.items.exists()


class ShopAdminSerializer(ShopSerializer):
    has_admin_notifications = serializers.SerializerMethodField()

    class Meta(ShopSerializer.Meta):
        fields = ShopSerializer.Meta.fields + ["has_admin_notifications"]

    def get_has_admin_notifications(self, obj):
        return obj.notifications.filter(type=NotificationType.ORDER_EVENT_ADMIN).exists()


class SetTelegramLinkSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    link = serializers.CharField()


class ChangeExchangeRateSerializer(serializers.Serializer):
    rate = serializers.IntegerField(min_value=1000)


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = "__all__"
        extra_kwargs = {"shop": {"write_only": True}}

        validators = [
            UniqueTogetherValidator(
                Admin.objects.all(),
                fields=["shop", "user"],
                message="User do'konga allaqachon admin qilingan",
            ),
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["user"] = UserSerializer(instance.user, context={"request": self.context.get("request")}).data

        return data
