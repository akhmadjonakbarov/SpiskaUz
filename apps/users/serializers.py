from django.contrib.sites.models import Site
from rest_framework import serializers

from .models import User
from ..role_manager.models import Role
from ..shops.models import Shop


class ShopSerializerForUser(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = '__all__'

    def get_role(self, obj):
        user = self.context.get('user')  # current logged-in user passed from view
        rule = Role.objects.filter(user=user, shop=obj).first()
        return rule.role if rule else None


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


class SimpleUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = serializers.SerializerMethodField()
    phone = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "first_name", "last_name",
            "phone", "avatar",
        ]

    def get_avatar(self, user: User):
        current_site = Site.objects.get_current()
        if user.avatar:
            return f"https://{current_site.domain}{user.avatar.url}"
        return None


class AdminMemberSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = serializers.SerializerMethodField()
    phone = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone", "avatar", ]

    def get_avatar(self, user: User):
        current_site = Site.objects.get_current()
        if user.avatar:
            return f"https://{current_site.domain}{user.avatar.url}"
        return None


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class CustomerSerializer(serializers.ModelSerializer):
    orders = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_orders(self, obj):
        # Import inside the method to prevent circular loops
        from apps.orders.serializers import OrderSerializer
        return OrderSerializer(obj.customer_orders.all(), many=True).data
