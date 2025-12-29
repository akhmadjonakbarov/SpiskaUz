from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.product_part.models import ProductPart
from apps.product_part.serializers import ProductPartSerializer, CreateProductPartSerializer, \
    UpdateProductPartSerializer


class ProductPartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product parts.

    list:
        Retrieve all product parts
    create:
        Create a new product part
    retrieve:
        Get a product part by ID
    update:
        Update a product part
    delete:
        Delete a product part
    """

    queryset = ProductPart.objects.filter(deleted_at=None).all()
    serializer_class = ProductPartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.all()
        shop_id = self.request.query_params.get('shop_id')
        product_id = self.request.query_params.get('product_id')
        is_confirm = self.request.query_params.get('is_confirm')

        if is_confirm is not None:
            if is_confirm.lower() in ['true', '1']:
                queryset = self.queryset.filter(is_confirm=True)
            elif is_confirm.lower() in ['false', '0']:
                queryset = self.queryset.filter(is_confirm=False)

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if product_id is not None:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shop_id', openapi.IN_QUERY, description="Filter by shop ID",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'product_id', openapi.IN_QUERY, description="Filter by product ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'is_confirm', openapi.IN_QUERY, description="Filter by confirming",
                type=openapi.TYPE_BOOLEAN
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateProductPartSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateProductPartSerializer
        return ProductPartSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_part = serializer.save(
            user=request.user
        )
        output_serializer = ProductPartSerializer(product_part)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance: ProductPart = self.get_object()
        if instance.is_confirm:
            return Response(
                {'detail': 'Cannot update a confirmed ProductPart.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        updated_part = serializer.save()
        output_serializer = ProductPartSerializer(updated_part, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        part: ProductPart = self.get_object()

        if part.is_confirm:
            return Response(
                {'detail': 'Cannot delete a confirmed ProductPart.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        part.soft_delete()
        return Response(
            {'detail': 'ProductPart was deleted'},
            status=status.HTTP_200_OK
        )
