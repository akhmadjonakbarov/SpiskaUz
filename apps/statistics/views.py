from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, status
from apps.document.models import DocumentItem


class BoughtStatisticView(APIView):
    def get(self):
        pass


class SoldStatisticView(APIView):
    queryset = DocumentItem.objects.all()
    permission_classes = (IsAuthenticated,)

    def get(self, request, shop_id):
        return Response(
            data={
                'detail': f'{shop_id}'
            }
        )
