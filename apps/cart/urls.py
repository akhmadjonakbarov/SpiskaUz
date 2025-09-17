from rest_framework.routers import DefaultRouter

from .views import CartItemViewSet, CartViewSet

router = DefaultRouter()
router.register("cart", CartViewSet)
router.register("cart-item", CartItemViewSet)


urlpatterns = router.urls + []
