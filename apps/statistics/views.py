from decimal import Decimal
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from typing import Dict
from apps.shops.models import Shop, ShopBalance
from apps.supplier.models import Supplier
from utils.convertor import Convertor
from apps.document.models import DocumentItem
from apps.document.serializers import DocumentItemSerializer
from apps.debt.models import Debt


class BaseStatisticView(GenericAPIView):
    serializer_class = None
    queryset = DocumentItem.objects.all()
    permission_classes = (IsAuthenticated,)
    doc_type = None

    def get_queryset(self):
        return DocumentItem.objects.filter(
            document__doc_type=self.doc_type, shop_id=self.kwargs['shop_id'], deleted_at=None
        ).order_by('-created_at')

    def get_shop(self):
        return Shop.objects.get(id=self.kwargs['shop_id'])

    def get_statistics(self, items, shop_id) -> Dict:

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            start_date = parse_date(start_date)  # or parse_datetime if datetime
            items = items.filter(created_at__gte=start_date)
        if end_date:
            end_date = parse_date(end_date)
            items = items.filter(created_at__lte=end_date)

        total_price = Decimal('0.0')
        total_income = Decimal('0.0')
        for doc_item in items:
            if doc_item.product.currency_type.lower() in 'usd':
                total_price = Convertor.to_decimal(
                    total_price) + doc_item.qty * doc_item.sale_price * doc_item.currency_rate_value

                total_income = Convertor.to_decimal(
                    total_income) + doc_item.qty * doc_item.income_price * doc_item.currency_rate_value
            else:
                total_price = Convertor.to_decimal(total_price) + doc_item.qty * doc_item.sale_price
                total_income = Convertor.to_decimal(total_income) + doc_item.qty * doc_item.income_price

        total_profit = Convertor.to_decimal(total_price) - Convertor.to_decimal(total_income)

        shop_profit = ShopBalance.objects.filter(shop_id=shop_id, deleted_at=None).first()

        if shop_profit is not None:
            total_profit = Convertor.to_decimal(total_profit) + Convertor.to_decimal(shop_profit.profit)

        return {
            'total_price': total_price,
            'total_profit': total_profit,
            'items': DocumentItemSerializer(items, many=True).data
        }


class BoughtStatisticView(BaseStatisticView):
    doc_type = 'buy'

    def get(self, request, shop_id):
        shop = self.get_shop()
        document_items = self.get_queryset()
        statistics = self.get_statistics(document_items, shop_id=shop.id)
        debt_price = self.get_debts(shop)
        statistics['debt_price'] = debt_price

        return Response(
            data=statistics
        )

    def get_debts(self, shop):
        from apps.currency_rate.models import CurrencyRate
        currency = CurrencyRate.objects.filter(shop=shop).order_by('-created_at').first()
        suppliers = shop.suppliers.all()
        total_debt = Decimal('0.0')

        if suppliers:
            for i in suppliers:
                balance = i.debt_balance
                total_debt = total_debt + Convertor.to_decimal(balance.balance_uzs)
                if balance.balance_usd > 0:
                    total_debt = Convertor.to_decimal(total_debt) + currency.rate * Convertor.to_decimal(
                        balance.balance_usd)

        return total_debt


class SoldStatisticView(BaseStatisticView):
    permission_classes = (IsAuthenticated,)
    doc_type = 'sell'

    def get(self, request, shop_id):
        shop = self.get_shop()
        document_items = self.get_queryset()

        statistics = self.get_statistics(document_items, shop_id=shop.id)
        statistics['debt_price'] = self.get_debts_price(shop)

        return Response(
            data=statistics
        )

    def get_debts_price(self, shop):
        debts = Debt.objects.filter(
            shop=shop, is_paid=False
        ).prefetch_related(
            "document__document_items"
        )

        payed_money = Decimal('0.0')
        total_price = Decimal('0.0')
        for d in debts:
            payed_money = payed_money + d.paid_money
            items = DocumentItem.objects.filter(
                document_id=d.document.id, deleted_at=None,
            )
            for i in items:
                if i.product.currency_type.lower() in 'usd':
                    total_price = total_price + i.sale_price * i.currency_rate_value * i.qty
                else:
                    total_price = total_price + i.sale_price * i.qty

        total_price = total_price - payed_money
        return total_price
