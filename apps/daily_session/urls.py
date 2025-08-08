from django.urls import path
from .views import CloseDayView, StartDayView

urlpatterns = [
    path('start/<uuid:shop_id>/', StartDayView.as_view()),
    path('close/<uuid:shop_id>/', CloseDayView.as_view()),
]
