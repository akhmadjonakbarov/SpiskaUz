from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.views import APIView

from .models import DailySession
from apps.shops.models import Shop


class StartDayView(APIView):
    queryset = DailySession.objects.all()

    def post(self, request, shop_id):
        today = timezone.localdate()
        shop = Shop.objects.get(id=shop_id)
        session = DailySession.objects.filter(
            shop=shop, date=today
        ).first()
        if session and session.is_open:
            return Response(data={
                'detail': 'Shop is already opened'
            })
        DailySession.objects.create(
            user=request.user, shop=shop, date=today
        )
        return Response(
            data={
                'detail': 'Shop is opened'
            }, status=status.HTTP_200_OK
        )


class CloseDayView(APIView):
    def post(self, request, shop_id):
        today = timezone.localdate()
        shop = Shop.objects.get(id=shop_id)
        session = DailySession.objects.filter(shop=shop, date=today).order_by('-date').first()
        session.close()
        return Response(
            data={
                'detail': 'Shop is closed'
            }, status=status.HTTP_200_OK
        )
