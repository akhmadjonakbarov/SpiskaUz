from decimal import Decimal
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from yaml import serialize

from apps.role_manager.models import Role
from apps.role_manager.serializer import CreateOrUpdateRoleSerializer, RoleSerializer
from apps.shops.models import Shop
from apps.users.models import User


class BaseRoleView(GenericAPIView):
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    permission_classes = (IsAuthenticated,)


class RoleListView(ListAPIView, BaseRoleView):

    def get_queryset(self):
        if not self.request.user.is_staff:
            return self.queryset.filter(created_by=self.request.user)
        return self.queryset.all()


class SetRoleView(BaseRoleView):
    serializer_class = CreateOrUpdateRoleSerializer

    def post(self, request):
        role = request.data.get('role')
        user_id = request.data.get('user')
        shop_id = request.data.get('shop')
        salary = request.data.get('salary')
        total_commission_percent = request.data.get('total_commission_percent', Decimal('0.0'))
        admin_commission_percent = request.data.get('admin_commission_percent', Decimal('0.0'))

        user = User.objects.get(id=user_id)
        shop = Shop.objects.get(id=shop_id)

        existed_role = Role.objects.filter(
            role=role, user=user, shop=shop
        ).first()
        if existed_role:
            existed_role.reset()
        else:
            Role.objects.create(
                user=user, shop=shop, role=role, created_by=request.user, salary=salary,
                total_commission_percent=total_commission_percent,
                admin_commission_percent=admin_commission_percent
            )
        return Response(
            data={
                'detail': f'{role} was set to {user.phone} successfully'
            }, status=status.HTTP_201_CREATED
        )


class UpdateRoleView(BaseRoleView):
    serializer_class = CreateOrUpdateRoleSerializer

    def patch(self, request, id):
        try:
            role = request.data.get('role')
            user_id = request.data.get('user')
            shop_id = request.data.get('shop')
            salary = request.data.get('salary')
            total_commission_percent = request.data.get('total_commission_percent', Decimal('0.0'))
            admin_commission_percent = request.data.get('admin_commission_percent', Decimal('0.0'))

            user = User.objects.get(id=user_id)
            shop = Shop.objects.get(id=shop_id)

            existed_role = self.queryset.filter(id=id).first()
            if existed_role is None:
                return Response(
                    data={
                        'detail': 'Role does not exist'
                    }, status=status.HTTP_404_NOT_FOUND
                )

            existed_role.role = role
            existed_role.user = user
            existed_role.shop = shop
            existed_role.salary = salary
            existed_role.total_commission_percent = total_commission_percent
            existed_role.admin_commission_percent = admin_commission_percent
            existed_role.save()
            serializer = RoleSerializer(existed_role, many=False)
            return Response(
                data={
                    'role': serializer.data
                }, status=status.HTTP_201_CREATED
            )
        except Role.DoesNotExist:
            return Response(
                data={
                    'detail': 'role does not exist'
                }, status=status.HTTP_404_NOT_FOUND
            )


class RemoveRoleView(BaseRoleView):

    def delete(self, request, id):
        try:
            role = self.queryset.get(id=id)
            role.soft_delete()
            return Response(
                data={
                    'detail': f'{role.role} was deleted successfully'
                }, status=status.HTTP_201_CREATED
            )
        except Role.DoesNotExist:
            return Response(
                data={
                    'detail': 'role does not exist'
                }, status=status.HTTP_404_NOT_FOUND
            )
