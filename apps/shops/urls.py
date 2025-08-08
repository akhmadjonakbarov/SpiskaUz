from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.admin import ShopAdminViewset
from .views.category import ShopCategoryViewSet
from .views.contact import ShopContactViewSet
from .views.shop import ShopDetailView, ShopViewSet
from .views.user_converstions import ShopUserConversionListView
from .views.user_order import ShopUserOrderListView
from .views.user_payments import ShopUserPaymentsListView

router = DefaultRouter()

router.register("shop", ShopViewSet)
router.register("shop-contact", ShopContactViewSet)
router.register("shop-category", ShopCategoryViewSet)
router.register("shop-admin", ShopAdminViewset)

urlpatterns = router.urls + [
    path("shop/<str:link>/", ShopDetailView.as_view(), name="shop_detail"),
    path("shop/<uuid:pk>/user/<uuid:customer_id>/orders/", ShopUserOrderListView.as_view(), name="shop-user-orders"),
    path("shop/<uuid:pk>/user/<uuid:customer_id>/payments/", ShopUserPaymentsListView.as_view(), name="shop-user-payments"),
    path("shop/<uuid:pk>/user/<uuid:customer_id>/conversions/", ShopUserConversionListView.as_view(), name="shop-user-conversions"),
]
