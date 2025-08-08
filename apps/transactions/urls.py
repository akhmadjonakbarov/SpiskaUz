from rest_framework.routers import DefaultRouter

from .views import TransactionViewSet

router = DefaultRouter()
router.register("transaction", TransactionViewSet)

urlpatterns = router.urls + []
