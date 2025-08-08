from django.urls import path
from .views import (
    CurrencyRateListView,
    CurrencyRateCreateView,
    CurrencyRateRetrieveView,
    CurrencyRateUpdateView,
    CurrencyRateDeleteView,
    LatestCurrencyRate,
)

urlpatterns = [
    path(
        'currency-rates/', CurrencyRateListView.as_view(
            {
                'get': 'list'
            }
        ),
        name='currencyrate-list'
    ),
    path(
        'currency-rates/latest/',
        LatestCurrencyRate.as_view(
            {'get': 'retrieve'}
        )
    ),
    path('currency-rates/create/', CurrencyRateCreateView.as_view(), name='currencyrate-create'),
    path('currency-rates/<int:pk>/', CurrencyRateRetrieveView.as_view(), name='currencyrate-detail'),
    path('currency-rates/<int:pk>/update/', CurrencyRateUpdateView.as_view(), name='currencyrate-update'),
    path('currency-rates/<int:pk>/delete/', CurrencyRateDeleteView.as_view(), name='currencyrate-delete'),
]
