# views.py

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Unit
from .serializers import UnitSerializer


class UnitListView(generics.GenericAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = (AllowAny,)

    def get(self, request):
        units = self.get_queryset()
        serializer = self.get_serializer(units, many=True)
        return Response(serializer.data)


class UnitCreateView(generics.GenericAPIView):
    serializer_class = UnitSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnitRetrieveView(generics.GenericAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    def get(self, request, pk):
        unit = self.get_object()
        serializer = self.get_serializer(unit)
        return Response(serializer.data)


class UnitUpdateView(generics.GenericAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    def put(self, request, pk):
        unit = self.get_object()
        serializer = self.get_serializer(unit, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        unit = self.get_object()
        serializer = self.get_serializer(unit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UnitDeleteView(generics.GenericAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    def delete(self, request, pk):
        unit = self.get_object()
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
