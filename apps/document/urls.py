from django.urls import path
from .views import SellProductView, BuyProductView, DocumentListView, DeleteSellDocumentView

urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
    path("/<int:pk>/delete/", DeleteSellDocumentView.as_view(), name="sell-product"),
    path("buy-product/", BuyProductView.as_view(), name="buy-product"),
    path("sell-product/", SellProductView.as_view(), name="sell-product"),
]
