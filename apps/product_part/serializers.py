from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers

from apps.currency_rate.models import CurrencyRate
from apps.currency_rate.serializers import CurrencyRateSerializer
from apps.product_part.models import ProductPart
from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from apps.supplier.serializers import SupplierSerializer

from apps.users.serializers import UserSerializer



class ProductPartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=False)
    currency_rate = CurrencyRateSerializer()
    confirmed_by = UserSerializer()
    supplier = SupplierSerializer()

    class Meta:
        model = ProductPart
        exclude = [
            'deleted_at', 'updated_at', 'user', 'shop',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        decimal_fields = [
            "qty",
            "income_price",
            "sale_price",
            "profit_as_percent",
            "currency_rate_value",
        ]

        for field in decimal_fields:
            value = data.get(field)
            if value is not None:
                try:
                    data[field] = float(value)
                except (ValueError, TypeError):
                    pass  # skip if conversion fails

        return data


class CreateProductPartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    income_price = serializers.FloatField(min_value=0)
    qty = serializers.FloatField(min_value=0.01)

    def create(self, validated_data):
        request = self.context.get("request")
        if not request:
            raise ValueError("Request context is required to assign created_by or confirmed_by")

        product_id = validated_data.pop("product_id")
        supplier = validated_data.pop("supplier")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found."})

        latest_rate = None
        currency_rate_value = None

        if product.currency_type.lower() == 'usd':
            latest_rate = self.get_latest_currency_rate(product.shop)
            currency_rate_value = latest_rate.rate

        # 🔒 Safe float-to-decimal conversion using str() wrapper
        sale_price = Decimal(str(product.sale_price))
        income_price = Decimal(str(validated_data["income_price"]))

        if income_price == Decimal("0.0"):
            profit_percent = Decimal("0.0")
        else:
            profit_percent = (
                    ((sale_price * Decimal("100")) / income_price) - Decimal("100")
            ).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)

        return ProductPart.objects.create(
            product=product,
            currency_rate=latest_rate,
            currency_rate_value=Decimal(str(currency_rate_value)) if currency_rate_value else Decimal('0.0'),
            user=request.user,
            shop=product.shop,
            profit_as_percent=profit_percent,
            supplier=supplier,
            income_price=income_price,
            sale_price=product.sale_price,
            qty=Decimal(str(validated_data["qty"])),
        )

    def get_latest_currency_rate(self, shop, currency='usd'):
        if currency.lower() == 'usd':
            latest_rate = CurrencyRate.objects.filter(shop=shop).order_by('-created_at').first()
            if latest_rate is None:
                raise serializers.ValidationError("No currency rate found for USD.")
            return latest_rate
        return Decimal('0.0')


class UpdateProductPartSerializer(serializers.Serializer):
    income_price = serializers.FloatField(min_value=0, required=False)
    qty = serializers.FloatField(min_value=0.01, required=False)
    currency_rate_id = serializers.IntegerField(required=False, allow_null=True)

    def update(self, instance, validated_data):
        request = self.context.get("request")

        # Update currency rate if provided
        currency_rate_id = validated_data.pop("currency_rate_id", None)
        if currency_rate_id is not None:
            if currency_rate_id:
                try:
                    currency_rate = CurrencyRate.objects.get(id=currency_rate_id)
                    instance.currency_rate = currency_rate
                    instance.currency_rate_value = currency_rate.rate
                except CurrencyRate.DoesNotExist:
                    raise serializers.ValidationError({"currency_rate_id": "Currency rate not found."})
            else:
                # Set currency_rate to None if explicitly null
                instance.currency_rate = None
                instance.currency_rate_value = None

        # Update simple fields
        for field in ['income_price', 'qty']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance
