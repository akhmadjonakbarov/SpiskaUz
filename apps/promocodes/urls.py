from rest_framework.routers import DefaultRouter

from .views import PromocodeItemViewSet, PromocodeViewSet

router = DefaultRouter()
router.register("promocode", PromocodeViewSet)
router.register("promocode-item", PromocodeItemViewSet)

urlpatterns = router.urls + []
