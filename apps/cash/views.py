from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CashHistory
from .permissions import IsShopOwnerOrAdmin
from .serializers import CashHistorySerializer


class CashHistoryViewSet(viewsets.ModelViewSet):
    queryset = CashHistory.objects.none()
    serializer_class = CashHistorySerializer
    permission_classes = (IsShopOwnerOrAdmin,)

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            pass
            # return CashHistory.objects.select_related("shop").filter(Q(shop__owner=user) | Q(shop__admins__user=user)).distinct()

        return self.queryset

    @action(
        methods=["get"],
        detail=True,
        url_path="by-shop",
        permission_classes=[IsShopOwnerOrAdmin],
    )
    def by_shop(self, request, pk=None):
        queryset = self.get_queryset().filter(shop_id=pk)

        if not queryset.exists():
            return Response(
                {"detail": "No cash history found for this shop."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
