from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.paginations import PageSizePagination
from common.serializers import EmptyBodySerializer

from .models import Advertisement, AdvertisementCategory
from .permissions import CanEditDeleteAdvertisement
from .serializers import (
    AdvertisementCategorySerializer,
    AdvertisementImageSerializer,
    AdvertisementSerializer,
    CreateUpdateAdvertisementSerializer,
)


class AdverticementViewSet(viewsets.ModelViewSet):
    """
    Reklamalarni boshqarish uchun ViewSet.

    list:
        Barcha reklamalarni olish
    create:
        Yangi reklama yaratish
    retrieve:
        ID bo'yicha reklamani olish
    update:
        Reklamani yangilash
    delete:
        Reklamani o'chirish
    upload_image:
        Reklama uchun rasm yuklash
    """

    queryset = Advertisement.objects.prefetch_related("favorited_by").all().order_by("-created_at")
    serializer_class = AdvertisementSerializer
    create_serializer_class = CreateUpdateAdvertisementSerializer
    permission_classes = [CanEditDeleteAdvertisement]
    search_fields = ["name", "description", "category__name"]
    pagination_class = PageSizePagination
    filterset_fields = ["published", "owner", "category"]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "published",
                openapi.IN_QUERY,
                description="Filter by published",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Filter by category",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "owner",
                openapi.IN_QUERY,
                description="Filter by owner ID",
                type=openapi.TYPE_INTEGER,
            ),
        ]
    )
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    def get_serializer_class(self):
        if self.action == "upload_image":
            return AdvertisementImageSerializer

        elif self.request.method in ["POST", "PUT", "PATCH"]:
            return self.create_serializer_class

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)

    @action(
        detail=False,
        methods=["POST"],
        url_path="upload-image",
        parser_classes=[FormParser, MultiPartParser],
        permission_classes=[IsAuthenticated],
    )
    def upload_image(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "published",
                openapi.IN_QUERY,
                description="Filter by published status (true or false)",
                type=openapi.TYPE_BOOLEAN,
            )
        ]
    )
    @action(["GET"], detail=False)
    def owned(self, request, *args, **kwargs):
        queryset = self.queryset.filter(owner=request.user)
        filtered = self.filter_queryset(queryset)

        page = self.paginate_queryset(filtered)

        if page is not None:
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filter, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(
        ["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="toggle-favorite",
        serializer_class=EmptyBodySerializer,
    )
    def toggle_favorite(self, request, pk=None):
        advertisement = self.get_object()
        user = request.user

        if advertisement in user.favorite_advertisements.all():
            user.favorite_advertisements.remove(advertisement)
            return Response({"detail": "Removed from favorites"}, status=status.HTTP_200_OK)
        else:
            user.favorite_advertisements.add(advertisement)
            return Response({"detail": "Added to favorites"}, status=status.HTTP_200_OK)

    @action(["GET"], detail=False, permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        advertisements = request.user.favorite_advertisements.all()
        serializer = self.get_serializer(advertisements, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AdvertisementCategoryViewSet(mixins.ListModelMixin, GenericViewSet):
    """
    Reklama kategoriyalarini ko'rish uchun ViewSet.

    list:
        Barcha reklama kategoriyalarini olish
    """

    queryset = AdvertisementCategory.objects.all()
    serializer_class = AdvertisementCategorySerializer
