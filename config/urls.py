from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from apps.users.views import well_known

schema_view = get_schema_view(
    openapi.Info(
        title="Spiska Uz API",
        default_version="v1",
        description="API for Spiska Uz",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

api_urls = [
    path("", include("apps.advertisements.urls")),
    path("", include("apps.cart.urls")),
    path("", include("apps.cash.urls")),
    path("", include("apps.debt.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.products.urls")),
    path("", include("apps.product_part.urls")),
    path("", include("apps.promocodes.urls")),
    path("", include("apps.currency_rate.urls")),
    path("", include("apps.unit.urls")),
    path("", include("apps.shops.urls")),
    path("", include("apps.supplier.urls")),
    path("documents/", include("apps.document.urls")),
    path("role-manager/", include("apps.role_manager.urls")),
    path("day/", include("apps.daily_session.urls")),
    path("store/", include("apps.store.urls")),
    path("", include("apps.transactions.urls")),
    path("auth/", include("apps.users.urls"), name="auth"),
]

urlpatterns = [
                  path("admin/", admin.site.urls),
                  path("api/v1/", include(api_urls)),
                  path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
                  path(".well-known/assetlinks.json", well_known),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
