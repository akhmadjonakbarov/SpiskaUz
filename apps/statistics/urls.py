from django.urls import path
from .views import SoldStatisticView, BoughtStatisticView

urlpatterns = [
    path(
        'bought/<int:shop_id>/', BoughtStatisticView.as_view()
    ),
    path(
        'sold/<int:shop_id>/', SoldStatisticView.as_view()
    ),
]
