from rest_framework.routers import DefaultRouter

from apps.product_part.views import ProductPartViewSet

router = DefaultRouter()
router.register("product-part", ProductPartViewSet)

urlpatterns = router.urls
