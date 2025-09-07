from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from apps.document.models import DocumentItemBalance
from apps.products.models import Product, ProductGroup, ProductImage, Report, ReportOption
from apps.shops.models import Shop, ShopCategory
from apps.shops.serializers import ShopCategorySerializer
from apps.unit.models import Unit
from apps.unit.serializers import UnitSerializer
from utils.convertor import Convertor


class ProductSerializerForDocumentItem(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"
        read_only_fields = ["product", ]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    category = ShopCategorySerializer(read_only=True)
    unit = UnitSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    qty = serializers.SerializerMethodField()
    # promocode = serializers.SerializerMethodField()
    profit_as_percent = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Product

        exclude = ('updated_at', 'deleted_at')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['discount'] = Convertor.to_float(instance.discount)
        data['sale_price'] = Convertor.to_float(instance.sale_price)
        return data

    def get_is_favorite(self, obj):
        request = self.context.get("request")

        user = request.user if request and hasattr(request, "user") else None

        if user:
            return user in obj.favorited_by.all()
        return False

    def get_qty(self, obj: Product):
        # Example filter: only consider active balances or a specific warehouse
        qty = DocumentItemBalance.objects.filter(product=obj).aggregate(total_qty=Sum('qty'))['total_qty']
        return qty or 0

    # def get_promocode(self, product):
    #     from apps.promocodes.serializers import PromocodeForProduct, Promocode
    #     promocode = Promocode.objects.filter(product=product).first()
    #     if promocode:
    #         return PromocodeForProduct(promocode, many=False).data
    #     return None

    def get_profit_as_percent(self, product: Product):
        total_percent = Decimal('0.0')
        balances = DocumentItemBalance.objects.filter(
            product=product, deleted_at=None,
        )

        if not balances:
            return Decimal('0.0')
        for balance in balances:
            total_percent = total_percent + Convertor.to_decimal(balance.profit_as_percent)

        middle_percent = total_percent / Decimal(balances.count())
        return middle_percent

    def get_currency(self, product):
        from apps.currency_rate.serializers import CurrencyRateSerializer, CurrencyRate
        balances = DocumentItemBalance.objects.filter(product=product).order_by('-created_at').last()
        if balances and balances.product.currency_type == 'usd':
            currency = CurrencyRateSerializer(balances.currency_rate)
            return currency.data
        else:
            currency = CurrencyRate.objects.filter(shop=product.shop).order_by('-created_at').first()
            currency_serializer = CurrencyRateSerializer(currency)
            return currency_serializer.data


class ProductReorderSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    ordered_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )

    def validate(self, data):
        category_id = data["category_id"]
        ordered_ids = data["ordered_ids"]

        # check products really belong to this category
        from .models import Product
        products = Product.objects.filter(id__in=ordered_ids, category_id=category_id)
        if products.count() != len(ordered_ids):
            raise serializers.ValidationError("Some products do not belong to this category.")

        return data

class ProductSerializerForUser(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    category = ShopCategorySerializer(read_only=True)
    unit = UnitSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    qty = serializers.SerializerMethodField()

    profit_as_percent = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Product

        exclude = ('updated_at', 'deleted_at')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['discount'] = Convertor.to_float(instance.discount)
        data['sale_price'] = Convertor.to_float(instance.sale_price)
        return data

    def get_is_favorite(self, obj):
        request = self.context.get("request")

        user = request.user if request and hasattr(request, "user") else None

        if user:
            return user in obj.favorited_by.all()
        return False

    def get_qty(self, obj: Product):
        # Example filter: only consider active balances or a specific warehouse
        qty = DocumentItemBalance.objects.filter(product=obj).aggregate(total_qty=Sum('qty'))['total_qty']
        return qty or 0

    def get_profit_as_percent(self, product: Product):
        total_percent = Decimal('0.0')
        balances = DocumentItemBalance.objects.filter(
            product=product, deleted_at=None,
        )

        if not balances:
            return Decimal('0.0')
        for balance in balances:
            total_percent = total_percent + Convertor.to_decimal(balance.profit_as_percent)

        middle_percent = total_percent / Decimal(balances.count())
        return middle_percent

    def get_currency(self, product):
        from apps.currency_rate.serializers import CurrencyRateSerializer, CurrencyRate
        currency = CurrencyRate.objects.filter(shop=product.shop).order_by('-created_at').first()
        currency_serializer = CurrencyRateSerializer(currency)
        return currency_serializer.data


class CreateProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('order', 'image', 'id')
        read_only_fields = ["product"]


class CreateProductSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )

    name = serializers.CharField(max_length=250, default="Name")
    description = serializers.CharField(max_length=1400, default="Description")
    sale_price = serializers.FloatField(default=0.0)
    barcode = serializers.CharField(max_length=20, default="Barcode")
    is_active = serializers.BooleanField(default=False)
    discount = serializers.FloatField(default=0.0)
    position = serializers.IntegerField(default=0)
    currency_type = serializers.CharField(default="uzs")
    shop = serializers.UUIDField()
    category = serializers.IntegerField()
    unit = serializers.IntegerField()
    group = serializers.UUIDField(required=False, allow_null=True)  # <-- now optional

    def validate_shop(self, value):
        try:
            return Shop.objects.get(pk=value)
        except Shop.DoesNotExist:
            raise serializers.ValidationError("Shop not found.")

    def validate_category(self, value):
        try:
            return ShopCategory.objects.get(pk=value)
        except ShopCategory.DoesNotExist:
            raise serializers.ValidationError("Category not found.")

    def validate_unit(self, value):
        try:
            return Unit.objects.get(pk=value)
        except Unit.DoesNotExist:
            raise serializers.ValidationError("Unit not found.")

    def validate_group(self, value):
        if not value:
            return None
        try:
            return ProductGroup.objects.get(pk=value)
        except ProductGroup.DoesNotExist:
            raise serializers.ValidationError("Group not found.")

    def create(self, validated_data):
        request = self.context["request"]
        images = validated_data.pop("images")
        shop = validated_data.pop("shop")
        category = validated_data.pop("category")
        unit = validated_data.pop("unit")
        group = validated_data.pop("group", None)

        if group is None:
            group = ProductGroup.objects.create(
                user=request.user,
                shop=shop,
                position=validated_data.get("position", 0)
            )

        product = Product.objects.create(
            shop=shop,
            user=request.user,
            category_id=category.id,
            unit_id=unit.id,
            group_id=group.id,
            **validated_data
        )

        # Attach images
        for image_id in images:
            ProductImage.objects.filter(id=image_id).update(product=product)

        return product

    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)

        category = validated_data.pop("category", None)
        unit = validated_data.pop("unit", None)
        group = validated_data.pop("group", None)

        if category:
            instance.category_id = category.id
        if unit:
            instance.unit_id = unit.id
        if group:
            instance.group_id = group.id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Re-link images if needed
        if images is not None:
            ProductImage.objects.filter(product=instance).update(product=None)
            ProductImage.objects.filter(id__in=images).update(product=instance)

        return instance


class SeparateProductsSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())


class CreateProductsGroupSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    target_product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False, allow_null=True)
    group = serializers.PrimaryKeyRelatedField(queryset=ProductGroup.objects.all(), required=False, allow_null=True)

    def validate(self, data):
        if not data.get("target_product") and not data.get("group"):
            raise serializers.ValidationError("Either 'target_product' or 'group' must be provided.")
        return data


class ProductPositionSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    position = serializers.IntegerField()


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        exclude = ["product", "user"]


class ReportOptionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = ReportOption
        fields = ["id", "title", "description", "options"]

    def get_options(self, obj):
        children = obj.options.all()
        if children.exists():
            return ReportOptionSerializer(children, many=True).data
        return []
