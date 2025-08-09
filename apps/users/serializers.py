from django.db.models import Sum
from rest_framework import serializers

from apps.notifications.models import NotificationType

from .models import User, RoleUser
from ..shops.models import Shop


class ShopSerializerForUser(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'


class BaseUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = serializers.ImageField(required=False)
    phone = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone", "avatar", ]


class UserSerializer(BaseUserSerializer):
    pass


class RoleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleUser
        fields = ('role', 'user', 'shop')


class SimpleUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = serializers.ImageField(required=False)
    phone = serializers.CharField(required=False, read_only=True)
    shops = ShopSerializerForUser(many=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "first_name", "last_name",
            "phone", "avatar", 'shops',
            "role"
        ]

    def get_role(self, obj):
        role_user = RoleUser.objects.filter(user=obj).first()
        return role_user.role if role_user else None


class AdminMemberSerializer(BaseUserSerializer):
    debt_in_uzs = serializers.SerializerMethodField()
    debt_in_usd = serializers.SerializerMethodField()
    total_debt = serializers.SerializerMethodField()
    total_converted_uzs = serializers.SerializerMethodField()
    total_converted_usd = serializers.SerializerMethodField()
    total_paid_uzs = serializers.SerializerMethodField()
    total_paid_usd = serializers.SerializerMethodField()
    has_notification = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            "debt_in_uzs",
            "debt_in_usd",
            "total_debt",
            "total_converted_uzs",
            "total_converted_usd",
            "total_paid_uzs",
            "total_paid_usd",
            "has_notification",
        ]

    def get_shop(self):
        return self.context.get("shop")

    def get_debt_in_uzs(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        total_debt_uzs = obj.customer_orders.filter(shop=shop).aggregate(total=Sum("debt"))["total"] or 0

        converted_uzs = obj.debt_conversions.filter(shop=shop, reverted=False).aggregate(total=Sum("amount_uzs"))[
                            "total"] or 0

        payments = obj.debt_payments.filter(shop=shop)
        total_paid_uzs = sum(p.amount_in_uzs for p in payments)

        return round(total_debt_uzs - converted_uzs - total_paid_uzs, 2)

    def get_debt_in_usd(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        debt_in_usd = obj.debt_conversions.filter(shop=shop, reverted=False).aggregate(total=Sum("amount_usd"))[
                          "total"] or 0

        return round(debt_in_usd, 2)

    def get_total_debt(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        return obj.customer_orders.filter(shop=shop).aggregate(total=Sum("debt"))["total"] or 0

    def get_total_converted_uzs(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        return obj.debt_conversions.filter(shop=shop, reverted=False).aggregate(total=Sum("amount_uzs"))["total"] or 0

    def get_total_converted_usd(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        return obj.debt_conversions.filter(shop=shop, reverted=False).aggregate(total=Sum("amount_usd"))["total"] or 0

    def get_total_paid_uzs(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        payments = obj.debt_payments.filter(shop=shop)
        return round(sum(p.amount_in_uzs for p in payments), 2)

    def get_total_paid_usd(self, obj):
        shop = self.get_shop()
        if not shop:
            return 0

        return obj.debt_payments.filter(shop=shop, currency="USD").aggregate(total=Sum("amount"))["total"] or 0

    def get_has_notification(self, obj):
        shop = self.get_shop()

        if not shop:
            return False

        return obj.notifications.filter(type=NotificationType.ORDER_EVENT_ADMIN, shop=shop).exists()


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
