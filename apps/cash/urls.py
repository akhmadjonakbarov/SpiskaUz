from rest_framework.routers import DefaultRouter

from .views import CashHistoryViewSet

router = DefaultRouter()
router.register("cash-history", CashHistoryViewSet)

urlpatterns = router.urls + []
