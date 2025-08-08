# urls.py

from django.urls import path
from .views import (
    UnitListView,
    UnitCreateView,
    UnitRetrieveView,
    UnitUpdateView,
    UnitDeleteView,
)

urlpatterns = [
    path('units/', UnitListView.as_view(), name='unit-list'),
    path('units/create/', UnitCreateView.as_view(), name='unit-create'),
    path('units/<int:pk>/detail/', UnitRetrieveView.as_view(), name='unit-detail'),
    path('units/<int:pk>/update/', UnitUpdateView.as_view(), name='unit-update'),
    path('units/<int:pk>/delete/', UnitDeleteView.as_view(), name='unit-delete'),
]
