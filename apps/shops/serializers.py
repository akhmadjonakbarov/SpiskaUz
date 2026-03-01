from django.contrib.sites.models import Site

from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.notifications.models import NotificationType
from apps.role_manager.models import Role
from apps.shops.models import Shop, Category, ShopContact
from apps.supplier.models import Supplier
from apps.users.serializers import UserSerializer, SimpleUserSerializer

from .models import Admin, ShopBalanceTransaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "image", "can_delete"]

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
    share_link = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    contacts = ShopContactSerializer(many=True, read_only=True)
    is_member = serializers.SerializerMethodField()
    has_notifications = serializers.SerializerMethodField()
    usd_exchange_rate = serializers.FloatField(write_only=True)  # or read_only=True if it's output only
    currency = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
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
            "currency",
            "role",
            "owner",
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
            shop=obj, date__day=today.day, date__year=today.year, date__month=today.month, is_open=True,
        ).order_by('-date').first()

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
        current_site = Site.objects.get_current()

        return f"https://{current_site.domain}/api/v1/shop/{obj.id}/"

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

    def get_owner(self, obj: Shop):

        role = Role.objects.filter(
            shop=obj, role='owner'
        ).first()
        serializer = SimpleUserSerializer(role.user)
        return serializer.data

    def get_role(self, obj):
        from apps.role_manager.serializer import RoleSerializer
        request = self.context.get("request")

        role = Role.objects.filter(
            user=request.user, shop=obj
        ).first()
        if role is None:
            return None
        return RoleSerializer(role, many=False).data


class ShopDetailSerializer(serializers.ModelSerializer):
    share_link = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    contacts = ShopContactSerializer(many=True, read_only=True)
    is_member = serializers.SerializerMethodField()
    has_notifications = serializers.SerializerMethodField()
    has_cart_item = serializers.SerializerMethodField()
    usd_exchange_rate = serializers.FloatField(write_only=True)  # or read_only=True if it's output only
    currency = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = "__all__"

    def get_is_open(self, obj):
        from apps.daily_session.models import DailySession
        today = timezone.now()
        session = DailySession.objects.filter(
            shop=obj, date__day=today.day, date__year=today.year, date__month=today.month, is_open=True,
        ).order_by('-date').first()

        if session is None:
            return False
        if session.is_open:
            return True
        else:
            return False

    def get_owner(self, obj: Shop):

        role = Role.objects.filter(
            shop=obj, role='owner'
        ).first()
        serializer = SimpleUserSerializer(role.user)
        return serializer.data

    def get_has_notifications(self, shop: Shop):
        user = self.context["request"].user
        return shop.notifications.filter(user=user).exists()

    def get_share_link(self, obj):
        current_site = Site.objects.get_current()

        return f"https://{current_site.domain}/api/v1/shop/{obj.id}/"

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

    def get_has_cart_item(self, instance: Shop):
        for cart in instance.carts.all():
            if cart.items.exists():
                return True
        return False


class ShopAdminSerializer(ShopSerializer):
    has_admin_notifications = serializers.SerializerMethodField()
    admin_type = serializers.SerializerMethodField()

    class Meta(ShopSerializer.Meta):
        fields = ShopSerializer.Meta.fields + ["has_admin_notifications", "admin_type"]

    def get_has_admin_notifications(self, obj):
        return obj.notifications.filter(type=NotificationType.ORDER_EVENT_ADMIN).exists()

    def get_admin_type(self, obj):
        from apps.shops.models import Admin
        user = self.context['request'].user

        admin = Admin.objects.filter(shop=obj, user=user).first()
        return admin.type


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


class ShopTransactionSerializer(serializers.ModelSerializer):
    created_by = SimpleUserSerializer(read_only=True)
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.filter(deleted_at=None), required=False,
    )
    transaction_type = serializers.SerializerMethodField()

    class Meta:
        model = ShopBalanceTransaction
        fields = '__all__'

    def get_transaction_type(self, transaction: ShopBalanceTransaction):
        if transaction.kind in ['profit', 'cash_income', 'cash_profit']:
            return 'income'
        else:
            return 'outcome'


class ShopBalanceCalculateSerializer(serializers.Serializer):
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.filter(deleted_at=None), required=False,
    )
    kind = serializers.ChoiceField(
        choices=[
            'loss', 'cash_loss', 'cash_profit', 'cash_income', 'cash_outcome', 'profit'
        ]
    )
    amount = serializers.DecimalField(
        max_digits=25, decimal_places=2
    )
    note = serializers.CharField(
        required=False
    )
    shop = serializers.PrimaryKeyRelatedField(
        queryset=Shop.actives.all()
    )


class ShopSerializerForRole(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'description', 'image')


class ShopMemberSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = Shop.members.through
        fields = ("id", "user", "shop", "is_admin")

    def get_is_admin(self, obj):
        return Role.objects.filter(
            user=obj.user,
            shop=obj.shop
        ).exists()
