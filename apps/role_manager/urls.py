from django.urls import path
from .views import SetRoleView, RemoveRoleView, RoleListView

urlpatterns = [
    path('', RoleListView.as_view(),
         ),
    path(
        'create/', SetRoleView.as_view(), ),
    path(
        'remove/<int:id>/', RemoveRoleView.as_view())
]
