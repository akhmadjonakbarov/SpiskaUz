from rest_framework.routers import DefaultRouter

from apps.salary.views import SalaryTransactionViewSet

router = DefaultRouter()
router.register(r'salary-transactions', SalaryTransactionViewSet, basename='salarytransaction')
urlpatterns = router.urls
