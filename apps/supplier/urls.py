from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, SupplierDebtPayView, SupplierDebtPaymentHistoryView

router = DefaultRouter()
router.register("supplier", SupplierViewSet)

urlpatterns = [
    path(
        'supplier/<int:id>/pay-debt/', SupplierDebtPayView.as_view()
    ),
    path(
        'supplier/<int:pk>/payment-history/', SupplierDebtPaymentHistoryView.as_view()
    )
]

urlpatterns += router.urls
