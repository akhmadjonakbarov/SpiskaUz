from decimal import Decimal
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from typing import Dict
from apps.shops.models import Shop, ShopBalance, ShopBalanceTransaction
from apps.supplier.models import Supplier
from utils.convertor import Convertor
from apps.document.models import DocumentItem, Document
from apps.document.serializers import DocumentItemSerializer, DocumentSerializer, DocumentSerializerForStatistic
from apps.debt.models import Debt
from django.db.models import Sum
from apps.shops.serializers import ShopTransactionSerializer


class BaseStatisticView(GenericAPIView):
    serializer_class = None
    queryset = Document.objects.all()
    permission_classes = (IsAuthenticated,)
    doc_type = None

    def get_queryset(self):
        return Document.objects.filter(
            doc_type=self.doc_type, shop_id=self.kwargs['shop_id'], deleted_at=None
        ).order_by('-created_at')

    def get_shop(self):
        return Shop.objects.get(id=self.kwargs['shop_id'])


class BoughtStatisticView(BaseStatisticView):
    doc_type = 'buy'

    def get(self, request, shop_id):
        shop = self.get_shop()
        documents = self.get_queryset()
        statistics = self.get_statistics(documents, shop_id=shop.id)
        debt_price = self.get_debts(shop)
        statistics['debt_price'] = debt_price

        return Response(
            data=statistics
        )

    @staticmethod
    def get_debts(shop):
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

    def get_statistics(self, documents, shop_id) -> Dict:
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            start_date = parse_date(start_date)  # or parse_datetime if datetime
            documents = documents.filter(created_at__gte=start_date)
        if end_date:
            end_date = parse_date(end_date)
            documents = documents.filter(created_at__lte=end_date)

        total_price = Decimal('0.0')
        total_income = Decimal('0.0')
        for document in documents:
            for doc_item in document.document_items.all():
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

        transactions = ShopBalanceTransaction.objects.filter(
            kind__in=('profit', 'cash_profit', 'cash_income'), shop_id=shop_id
        )
        transactions_data = ShopTransactionSerializer(transactions, many=True).data
        for t in transactions_data:
            t['type'] = 'transaction'

        documents_data = DocumentSerializer(documents, many=True).data
        for d in documents_data:
            d['type'] = 'document'

        return {
            'total_price': total_price,
            'total_profit': total_profit,
            'items': transactions_data + documents_data,
        }


class SoldStatisticView(BaseStatisticView):
    permission_classes = (IsAuthenticated,)
    doc_type = 'sell'

    def get(self, request, shop_id):
        shop = self.get_shop()
        total_debt = self.get_total_debt(shop)
        removed_profit = self.get_total_price_removed_profit(shop)
        removed_cash = self.get_total_price_removed_cash(shop)

        transactions = ShopBalanceTransaction.objects.filter(
            shop=shop, kind__in=['cash_loss', 'loss', 'cash_outcome'], deleted_at=None
        )

        documents = self.get_queryset()

        transactions_data = ShopTransactionSerializer(transactions, many=True).data
        for t in transactions_data:
            t['type'] = 'transaction'

        document_items_data = DocumentSerializerForStatistic(documents, many=True).data
        for d in document_items_data:
            d['type'] = 'document'

        return Response(
            data={
                'items': transactions_data + document_items_data,
                'total_debt': total_debt,
                'removed_profit': removed_profit,
                'removed_cash': removed_cash
            }
        )

    @staticmethod
    def get_total_debt(shop):
        from apps.currency_rate.models import CurrencyRate
        suppliers = Supplier.objects.filter(shops=shop)

        balance_usd = Decimal('0.0')
        balance_uzs = Decimal('0.0')

        for supplier in suppliers:
            balance = supplier.debt_balance
            balance_usd = balance_usd + balance.balance_usd
            balance_uzs = balance_uzs + balance.balance_uzs

        currency = CurrencyRate.objects.filter(shop=shop).order_by('-created_at').first()
        balance_uzs = balance_uzs + balance_usd * currency.rate

        return balance_uzs

    @staticmethod
    def get_total_price_removed_profit(shop) -> Decimal:
        result = ShopBalanceTransaction.objects.filter(
            kind='loss', shop=shop
        ).aggregate(total=Sum("amount"))
        total = result["total"] or Decimal("0")
        return Convertor.to_decimal(total)

    @staticmethod
    def get_total_price_removed_cash(shop) -> Decimal:
        result = ShopBalanceTransaction.objects.filter(
            kind='cash_loss', shop=shop
        ).aggregate(total=Sum("amount"))
        total = result["total"] or Decimal("0")
        return Convertor.to_decimal(total)

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
