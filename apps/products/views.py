import random

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from common.serializers import EmptyBodySerializer
from .models import Product, ReportOption
from .serializers import ProductSerializer, CreateProductSerializer, CreateProductImageSerializer, ReportSerializer, \
    ReportOptionSerializer, ProductSerializerForUser, ProductReorderSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    Mahsulotlarni boshqarish uchun ViewSet.

    list:
        Barcha mahsulotlarni olish
    create:
        Yangi mahsulot yaratish
    retrieve:
        ID bo'yicha mahsulotni olish
    update:
        Mahsulotni yangilash
    delete:
        Mahsulotni o'chirish
    upload_image:
        Mahsulot uchun rasm yuklash
    """

    filter_fields = ('shop_id',)

    queryset = Product.objects.prefetch_related("favorited_by").filter(deleted_at=None).all()
    serializer_class = ProductSerializer
    create_serializer_class = CreateProductSerializer
    permission_classes = [IsAuthenticated, ]

    def get_serializer_class(self):
        if self.action == "upload_image":
            return CreateProductImageSerializer

        elif self.action == "add_report":
            return ReportSerializer

        elif self.request.method in ["POST", "PUT", "PATCH"]:
            return self.create_serializer_class

        return self.serializer_class

    @action(detail=False, methods=["POST"], url_path="upload-image", parser_classes=[FormParser, MultiPartParser],
            permission_classes=[IsAuthenticated])
    def upload_image(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        existed_product = Product.objects.filter(barcode=request.data['barcode']).first()
        if existed_product:
            return Response(
                data={
                    'detail': 'The barcode already exist',
                }, status=409
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        # ProductGroup.objects.create()

        output_serializer = ProductSerializer(product, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Use write serializer (e.g., CreateProductSerializer) for input
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        # Use read serializer (e.g., ProductSerializer) for output
        output_serializer = ProductSerializer(product, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(["POST"], detail=True, permission_classes=[IsAuthenticated], url_path="toggle-favorite",
            serializer_class=EmptyBodySerializer)
    def toggle_favorite(self, request, pk=None):
        product = self.get_object()
        user = request.user
        if product in user.favorite_products.all():
            user.favorite_products.remove(product)
            return Response({"detail": "Removed from favorites"}, status=status.HTTP_200_OK)
        else:
            user.favorite_products.add(product)
            return Response({"detail": "Added to favorites"}, status=status.HTTP_200_OK)

    @action(["GET"], detail=False, permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        products = request.user.favorite_products.all()
        serializer = ProductSerializerForUser(products, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(["GET"], detail=True, permission_classes=[IsAuthenticated])
    def simillar(self, request, pk=None):
        product = self.get_object()

        if product.group is not None:
            products = Product.objects.prefetch_related("images", "parts", "favorited_by").filter(
                group=product.group).exclude(id=product.id)
        else:
            products = []

        serializer = self.get_serializer(products, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(["GET"], detail=False, url_path="generate-barcode")
    def generate_barcode(self, request, *args, **kwargs):
        while True:
            barcode = "".join([str(random.randint(0, 9)) for _ in range(13)])

            if not self.queryset.filter(barcode=barcode).exists():
                return Response({"barcode": barcode}, status=status.HTTP_200_OK)

    @action(["POST"], detail=True, permission_classes=[IsAuthenticated])
    def add_report(self, request, pk=None):
        product = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, product=product)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        shop_id = self.request.query_params.get('shop')
        queryset = Product.objects.all()
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shop_id', openapi.IN_QUERY,
                description="Filter by shop ID",
                type=openapi.TYPE_STRING
            )
        ]
    )
    def list(self, request: Request, *args, **kwargs):
        products = self.get_queryset().filter(
            shop_id=request.query_params.get('shop_id')
        )
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.soft_delete()
        return Response(
            data={
                'detail': 'Product was deleted'
            }, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        request_body=ProductReorderSerializer
    )
    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = ProductReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category_id = serializer.validated_data["category_id"]
        ordered_ids = serializer.validated_data["ordered_ids"]

        # update positions
        for index, product_id in enumerate(ordered_ids, start=1):
            Product.objects.filter(id=product_id, category_id=category_id).update(position_number=index)

        products = Product.objects.filter(category_id=category_id).order_by("position_number")
        return Response(ProductSerializer(products, many=True).data)


class ReportOptionListAPIView(ListAPIView):
    queryset = ReportOption.objects.filter(parent__isnull=True).prefetch_related("options")
    serializer_class = ReportOptionSerializer
    permission_classes = [IsAuthenticated]
