from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser

from apps.shops.models import Category
from apps.shops.serializers import CategorySerializer


class ShopCategoryViewSet(viewsets.ModelViewSet):
    """
    Do'kon kategoriyalarini boshqarish uchun ViewSet.

    list:
        Barcha do'kon kategoriyalarini olish
    create:
        Yangi do'kon kategoriyasi yaratish
    retrieve:
        ID bo'yicha do'kon kategoriyasini olish
    update:
        Do'kon kategoriyasini yangilash
    delete:
        Do'kon kategoriyasini o'chirish
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    parser_classes = [FormParser, MultiPartParser]

    def perform_destroy(self, instance):
        if not instance.can_delete:
            raise ValidationError({"message": "Umumiy categoriyani o'chirib bo'lmaydi"})

        return super().perform_destroy(instance)
