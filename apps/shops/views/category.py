from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser

from apps.shops.models import ShopCategory
from apps.shops.serializers import ShopCategorySerializer


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

    queryset = ShopCategory.objects.all()
    serializer_class = ShopCategorySerializer
    parser_classes = [FormParser, MultiPartParser]

    def perform_destroy(self, instance):
        if not instance.can_delete:
            raise ValidationError({"message": "Umumiy categoriyani o'chirib bo'lmaydi"})

        return super().perform_destroy(instance)
