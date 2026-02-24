from rest_framework import viewsets
from rest_framework.generics import GenericAPIView


# Create your views here.
class BaseViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = self.queryset
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset


class BaseGenericAPIView(GenericAPIView):

    def get_queryset(self):
        queryset = self.queryset
        shop_id = self.request.query_params.get('shop_id')
        product_id = self.request.query_params.get('product_id')

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if product_id is not None:
            queryset = queryset.filter(product_id=product_id)
        return queryset
