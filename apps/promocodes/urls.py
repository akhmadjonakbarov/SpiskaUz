from rest_framework.routers import DefaultRouter

from .views import PromoCodeItemViewSet, PromoCodeViewSet

router = DefaultRouter()
router.register("promocode", PromoCodeViewSet)
router.register("promocode-item", PromoCodeItemViewSet)

urlpatterns = router.urls + []
