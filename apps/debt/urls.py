from rest_framework.routers import DefaultRouter

from .views import DebtConversionViewSet, DebtPaymentViewSet

router = DefaultRouter()
router.register("debt/conversion", DebtConversionViewSet)
router.register("debt/payment", DebtPaymentViewSet)


urlpatterns = router.urls + []
