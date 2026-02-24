from django.urls import path
from .views import StoreView, StoreByShop

urlpatterns = [
    path("all/", StoreView.as_view()),
    path(
        "by-shop/<int:shop_id>/", StoreByShop.as_view(
            {
                'get': 'retrieve'
            }
        ),
    )
]
