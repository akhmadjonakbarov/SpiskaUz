from django.urls import path
from .views import SoldStatisticView, BoughtStatisticView

urlpatterns = [
    path(
        'bought/<str:shop_id>/', BoughtStatisticView.as_view()
    ),
    path(
        'sold/<str:shop_id>/', SoldStatisticView.as_view()
    ),
]
