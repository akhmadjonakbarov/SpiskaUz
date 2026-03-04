from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SeasonViewSet

router = DefaultRouter()
router.register(r'game', SeasonViewSet, basename='game')

urlpatterns = [
    path('', include(router.urls)),
]
