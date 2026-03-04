import secrets
import string

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PromoCode, PromoCodeItem
from .serializers import PromoCodeItemSearchSerializer, PromoCodeCreateSerializer
from .serializers import PromoCodeItemSerializer, PromoCodeSerializer


def generate_promo_code(length=6):
    # We use uppercase letters and digits, excluding ambiguous characters like '0', 'O', '1', 'I'
    # if you want to make it extra user-friendly.
    characters = string.ascii_uppercase + string.digits

    # Generate a cryptographically strong random string
    code = ''.join(secrets.choice(characters) for _ in range(length))

    return code


class PromoCodeViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = PromoCode.objects.none()
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PromoCode.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return PromoCodeCreateSerializer
        return PromoCodeSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 1. Validate data using the Create Serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Extract data
        items_data = serializer.validated_data.pop('items', [])
        shop = serializer.validated_data['shop']

        # 3. Create the PromoCode with a generated code
        # We handle uniqueness by checking if the code exists
        unique_code = generate_promo_code()
        while PromoCode.objects.filter(code=unique_code).exists():
            unique_code = generate_promo_code()

        promo_code = PromoCode.objects.create(
            shop=shop,
            created_by=self.request.user,
            code=unique_code,
            is_active=serializer.validated_data.get('is_active', True)
        )

        # 4. Bulk create the items
        promo_items = [
            PromoCodeItem(
                promo_code=promo_code,
                product=item['product'],  # Use 'product_id' if that's the key in your CreateItemSerializer
                discount=item['discount']
            )
            for item in items_data
        ]

        if promo_items:
            PromoCodeItem.objects.bulk_create(promo_items)

        # 5. Return the result using the READ serializer (PromoCodeSerializer)
        # This ensures the user gets the full nested detail immediately.
        output_serializer = PromoCodeSerializer(promo_code)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        # Soft delete implementation
        instance.is_active = False
        instance.save()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "shop", openapi.IN_QUERY, description="Shop name", type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                "code", openapi.IN_QUERY, description="PromoCode code", type=openapi.TYPE_STRING,
                required=True
            ),
        ]
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        shop = request.query_params.get("shop")
        code = request.query_params.get("code")

        if not shop or not code:
            return Response({"detail": "shop and code are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            promocode = self.get_queryset().get(shop=shop, code=code)
        except PromoCode.DoesNotExist:
            return Response({"detail": "Promocode topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if not promocode.can_use_promocode(request.user):
            return Response({"detail": "Siz ushbu promokodni allaqachon ishlatgansiz."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(promocode)

        return Response(serializer.data)


class PromoCodeItemViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = PromoCodeItem.objects.all()
    serializer_class = PromoCodeItemSerializer

    def get_serializer_class(self):
        # Dynamically switch serializer based on the action name
        if self.action == 'check_validity':
            return PromoCodeItemSearchSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='check-validity')
    def check_validity(self, request):
        # 1. Validate input using your SearchSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Extract validated data
        code_text = serializer.validated_data['promo_code']
        product_identifier = serializer.validated_data['product_id']

        # 3. Query the Database
        # Note: We filter by the code string and the product (ID or Name)
        promo_item = PromoCodeItem.objects.filter(
            promo_code__code=code_text,
            promo_code__is_active=True,
            product_id=product_identifier  # Assuming 'product' passed is the ID
        ).select_related('promo_code', 'product').first()

        # 4. Business Logic Validation
        if not promo_item:
            return Response(
                {"error": "Promo code not found for this product."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not promo_item.promo_code.can_use_promo_code(request.user):
            return Response(
                {"error": "You have already used this promo code."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 5. Return success data
        return Response({
            "valid": True,
            "discount": promo_item.discount,
            "code": promo_item.promo_code.code,
            "shop": promo_item.promo_code.shop.id
        }, status=status.HTTP_200_OK)
