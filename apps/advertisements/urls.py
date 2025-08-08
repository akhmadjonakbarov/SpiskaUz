from rest_framework.routers import DefaultRouter

from .views import AdverticementViewSet, AdvertisementCategoryViewSet

router = DefaultRouter()
router.register("advertisement", AdverticementViewSet)
router.register("advertisement-category", AdvertisementCategoryViewSet)

urlpatterns = router.urls + []
