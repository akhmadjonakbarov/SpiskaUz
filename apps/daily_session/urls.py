from django.urls import path
from .views import CloseDayView, StartDayView

urlpatterns = [
    path('start/<int:shop_id>/', StartDayView.as_view()),
    path('close/<int:shop_id>/', CloseDayView.as_view()),
]
