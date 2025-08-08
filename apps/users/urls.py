from django.urls import include, path

from .routers import router
from .views import logout_page

urlpatterns = [
    path("logout/", logout_page, name="logout"),
    path("", include("rest_framework.urls", namespace="rest_framework")),
    path("", include(router.urls)),
]
