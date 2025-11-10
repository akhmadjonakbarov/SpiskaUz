from django.urls import path


from .views import SetRoleView, RemoveRoleView, RoleListView, UpdateRoleView, DetailRoleView



urlpatterns = [
    path('', RoleListView.as_view(),
         ),
    path(
        'create/', SetRoleView.as_view(), ),
    path(
        'detail/<int:pk>/', DetailRoleView.as_view()),
    path(
        'update/<int:id>/', UpdateRoleView.as_view()),
    path(
        'remove/<int:id>/', RemoveRoleView.as_view())
]

