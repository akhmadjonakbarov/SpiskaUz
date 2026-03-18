from apps.products.models import Category
from apps.shops.serializers import CategorySerializer, CreateCategorySerializer

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser


class ShopCategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    parser_classes = [FormParser, MultiPartParser]

    def get_serializer_class(self):

        if self.action == 'create':
            return CreateCategorySerializer
        return CategorySerializer

    def get_queryset(self):

        qs = super().get_queryset()
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            return qs.filter(shop_id=shop_id)
        return qs

    def perform_create(self, serializer):

        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = serializer.save(user=self.request.user)

        output_serializer = CategorySerializer(category)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.can_delete:
            if 'name' in request.data and request.data['name'] != instance.name:
                raise ValidationError({"detail": "Protected category names cannot be changed."})

        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):

        if not instance.can_delete:
            raise ValidationError({"detail": "Umumiy categoriyani o'chirib bo'lmaydi"})

        instance.delete()
