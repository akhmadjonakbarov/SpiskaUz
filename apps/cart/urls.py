from rest_framework.routers import DefaultRouter

from .views import ShoppingCartItemViewSet, ShoppingCartViewSet

router = DefaultRouter()
router.register("cart", ShoppingCartViewSet)
router.register("cart-item", ShoppingCartItemViewSet)


urlpatterns = router.urls + []
