from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, ReportOptionListAPIView

router = DefaultRouter()
router.register("product", ProductViewSet)



urlpatterns = router.urls + [
    path("report-options/", ReportOptionListAPIView.as_view()),
]
