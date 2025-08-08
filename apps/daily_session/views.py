from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from .models import DailySession
from apps.shops.models import Shop


class StartDayView(GenericAPIView):
    queryset = DailySession.objects.all()

    def post(self, request, shop_id):
        today = timezone.localdate()
        shop = Shop.objects.get(id=shop_id)
        session = DailySession.objects.get(
            shop=shop, date=today
        )
        if session:
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


class CloseDayView(GenericAPIView):
    def post(self, request, shop_id):
        today = timezone.localdate()
        shop = Shop.objects.get(id=shop_id)
        session = DailySession.objects.get(shop=shop, date=today)
        session.is_open = False
        session.save()
        return Response(
            data={
                'detail': 'Shop is closed'
            }, status=status.HTTP_200_OK
        )
