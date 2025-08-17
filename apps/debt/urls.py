from rest_framework.routers import DefaultRouter

from .views import DebtConversionViewSet, DebtPaymentViewSet, DebtViewSet

router = DefaultRouter()
# router.register("debt/conversion", DebtConversionViewSet)
# router.register("debt/payment", DebtPaymentViewSet)
router.register("debt/client", DebtViewSet)

urlpatterns = router.urls + []
