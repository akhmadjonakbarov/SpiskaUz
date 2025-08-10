from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from apps.role_manager.models import RoleUser
from apps.role_manager.serializer import CreateRoleSerializer, RoleUserSerializer
from apps.shops.models import Shop
from apps.users.models import User


class BaseRoleView(GenericAPIView):
    serializer_class = RoleUserSerializer
    queryset = RoleUser.objects.all()
    permission_classes = (IsAuthenticated,)


class RoleListView(ListAPIView, BaseRoleView):

    def get_queryset(self):
        if not self.request.user.is_staff:
            return self.queryset.filter(created_by=self.request.user)
        return self.queryset.all()


class SetRoleView(BaseRoleView):
    serializer_class = CreateRoleSerializer

    def post(self, request):
        role = request.data.get('role')
        user_id = request.data.get('user')
        shop_id = request.data.get('shop')
        user = User.objects.get(id=user_id)
        shop = Shop.objects.get(id=shop_id)
        RoleUser.objects.create(
            user=user, shop=shop, role=role, created_by=request.user
        )
        return Response(
            data={
                'detail': f'{role} was set to {user.phone} successfully'
            }, status=status.HTTP_201_CREATED
        )


class RemoveRoleView(BaseRoleView):

    def delete(self, request, id):
        try:
            role = self.queryset.get(id)
            return Response(
                data={
                    'detail': f'{role.role} was deleted successfully'
                }, status=status.HTTP_201_CREATED
            )
        except RoleUser.DoesNotExist:
            return Response(
                data={
                    'detail': 'role does not exist'
                }, status=status.HTTP_404_NOT_FOUND
            )
