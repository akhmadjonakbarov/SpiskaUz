from decimal import Decimal
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from typing import Dict
from apps.shops.models import Shop, ShopBalance, ShopBalanceTransaction
from apps.statistics.services.debt_calculator import SupplierDebtCalculatorService
from utils.convertor import Convertor
from apps.document.models import DocumentItem, Document, DocumentOrder
from apps.debt.models import Debt
from django.db.models import Sum


class BaseStatisticView(GenericAPIView):
    serializer_class = None
    queryset = Document.actives.all()
    permission_classes = (IsAuthenticated,)
    doc_type = None

    def get_queryset(self):
        return Document.actives.filter(
            doc_type=self.doc_type, shop_id=self.kwargs['shop_id'],
        ).order_by('-created_at')

    def get_shop(self):
        return Shop.objects.get(id=self.kwargs['shop_id'])


class BoughtStatisticView(BaseStatisticView):
    doc_type = 'buy'

    def get(self, request, shop_id):
        shop = self.get_shop()
        documents = self.get_queryset()
        total_debt = SupplierDebtCalculatorService(shop).calculate()
        total_price = self.get_total_price(documents)
        removed_profit = self.get_total_price_removed_profit(shop)
        removed_cash = self.get_total_price_removed_cash(shop)

        data = {
            'total_price': total_price,
            'total_debt': total_debt,
            'removed_profit': removed_profit,
            'removed_cash': removed_cash,
        }

        return Response(
            data=data
        )

    def get_total_price(self, documents):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            start_date = parse_date(start_date)  # or parse_datetime if datetime
            documents = documents.filter(created_at__gte=start_date)
        if end_date:
            end_date = parse_date(end_date)
            documents = documents.filter(created_at__lte=end_date)

        total_price = Decimal('0.0')
        for document in documents:
            for doc_item in document.document_items.all():
                if doc_item.product.currency_type.lower() in 'usd':
                    total_price = Convertor.to_decimal(
                        total_price) + doc_item.qty * doc_item.income_price * doc_item.currency_rate_value
                else:
                    total_price = Convertor.to_decimal(total_price) + doc_item.qty * doc_item.income_price

        return total_price

    @staticmethod
    def get_debts(shop):
        from apps.currency_rate.models import CurrencyRate
        currency = (
            CurrencyRate.actives.filter(shop=shop).order_by('-created_at').first()
        )
        total_debt = Decimal('0.0')

        for i in shop.suppliers.all():
            balance = i.debt_balance
            total_debt += Convertor.to_decimal(balance.balance_uzs)
            if balance.balance_usd > 0 and currency:
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

        shop_profit = ShopBalance.actives.filter(shop_id=shop_id).first()

        if shop_profit is not None:
            total_profit = Convertor.to_decimal(total_profit) + Convertor.to_decimal(shop_profit.profit)

        return {
            'total_price': total_price,
            'total_profit': total_profit,
        }

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


class SoldStatisticView(BaseStatisticView):
    permission_classes = (IsAuthenticated,)
    doc_type = 'sell'

    def get(self, request, shop_id):
        shop = self.get_shop()
        total_price = self.get_total_price(shop)
        discount = self.get_total_discount(shop)
        total_profit = self.get_total_profit(shop)

        data = {
            'total_price': total_price,
            'discount': discount,
            'agreed_price': Decimal('0.0'),
            'amount_cash': Decimal('0.0'),
            'debt': Decimal('0.0'),
            'total_profit': total_profit,
        }

        return Response(
            data=data
        )

    def get_total_price(self, shop):
        total_price = Decimal('0.0')
        documents = Document.actives.filter(shop=shop, doc_type=self.doc_type).prefetch_related("document_items")
        for document in documents:
            document_items = document.document_items.all()
            for doc_item in document_items:
                if doc_item.product.currency_type.lower() in 'usd':
                    total_price = Convertor.to_decimal(
                        total_price) + doc_item.qty * doc_item.sale_price * doc_item.currency_rate_value
                else:
                    total_price = Convertor.to_decimal(total_price) + doc_item.qty * doc_item.sale_price

        return total_price

    def get_total_income_price(self, shop):
        total_income_price = Decimal('0.0')
        documents = Document.actives.filter(shop=shop, doc_type=self.doc_type).prefetch_related("document_items")
        for document in documents:
            document_items = document.document_items.all()
            for doc_item in document_items:
                if doc_item.product.currency_type.lower() in 'usd':
                    total_income_price = Convertor.to_decimal(
                        total_income_price) + doc_item.qty * doc_item.income_price * doc_item.currency_rate_value
                else:
                    total_income_price = Convertor.to_decimal(total_income_price) + doc_item.qty * doc_item.income_price
        return total_income_price

    def get_total_profit(self, shop):
        return self.get_total_price(shop) - self.get_total_income_price(shop)

    def get_total_discount(self, shop) -> Decimal:
        total_discount = Decimal('0.0')
        documents = Document.actives.filter(shop=shop, doc_type=self.doc_type).prefetch_related("document_items")
        for document in documents:
            payment_detail = document.payment_detail
            total_discount = total_discount + Convertor.to_decimal(payment_detail.discount)
        return total_discount

    def get_total_debt(self, shop):
        documents = (
            Document.actives
            .filter(
                shop=shop,
                doc_type=self.doc_type,
                documentorder__isnull=False  # INNER JOIN
            )
            .select_related("documentorder", "documentorder__order")
            .prefetch_related("document_items")
        )
        for document in documents:
            order = document.order

        return Decimal('0.0')

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
