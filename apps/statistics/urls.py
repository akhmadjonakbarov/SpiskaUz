from django.urls import path
from .views import SoldStatisticView

urlpatterns = [
    path(
        'sold/<str:shop_id>/', SoldStatisticView.as_view()
    ),
]
