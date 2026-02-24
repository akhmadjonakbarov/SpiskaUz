from decimal import Decimal

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.admin_panel.services import SalaryCalculatorService
from apps.currency_rate.models import CurrencyRate
from apps.document.factories.document_factory import DocumentFactory, PaymentInfoData, PaymentDetailData
from apps.document.models import Document, DocumentItem, DocumentItemBalance
from apps.document.serializers import DocumentSerializer, BuyProductSerializer, SellProductSerializer
from apps.document.utils.calculator import Calculator
from apps.product_part.models import ProductPart
from apps.products.models import Product
from apps.promocodes.models import PromoCode
from apps.supplier.models import SupplierDebtBalance, SupplierTransaction
from apps.users.models import User
from constants.currency_choices import CURRENCY_USD
from utils.convertor import Convertor
from apps.supplier.models import Supplier


class DocumentListView(GenericAPIView):
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()

    def get_queryset(self):
        queryset = self.queryset.all()
        shop_id = self.request.query_params.get('shop_id')
        product_id = self.request.query_params.get('product_id')

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if product_id is not None:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shop_id', openapi.IN_QUERY, description="Filter by shop ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'product_id', openapi.IN_QUERY, description="Filter by product ID",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        documents = self.get_queryset()
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)


class DeleteSellDocumentView(GenericAPIView):
    serializer_class = DocumentSerializer
    queryset = Document.actives.all()

    def delete(self, request, pk):
        document = self.get_queryset().filter(id=pk).first()
        if document is None:
            return Response({"message": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        document_items = document.document_items.all()
        with transaction.atomic():
            for document_item in document_items:
                doc_item: DocumentItem = document_item
                product_balance: DocumentItemBalance = DocumentItemBalance.objects.filter(
                    product=doc_item.product,
                    shop=doc_item.shop,
                    currency_rate=doc_item.currency_rate,
                    income_price=doc_item.income_price
                ).select_for_update().first()
                print(f"Product Balance: {product_balance}")
                if product_balance:
                    product_balance.qty += Decimal(str(doc_item.qty))
                    product_balance.save()

                else:
                    # 1️⃣ Create new document (stock IN)
                    refurbish_document = Document.objects.create(
                        doc_type='buy',  # stock comes back
                        shop=document.shop,
                        user=request.user,
                        supplier=None,
                    )
                    # Create document item
                    refurbish_item = DocumentItem.objects.create(
                        document=refurbish_document,
                        product=doc_item.product,
                        qty=doc_item.qty,
                        income_price=doc_item.income_price,
                        sale_price=doc_item.sale_price,
                        currency_rate=doc_item.currency_rate,
                        currency_rate_value=doc_item.currency_rate_value,
                        profit_as_percent=doc_item.profit_as_percent,
                        shop=doc_item.shop,
                        user=doc_item.user,
                    )

                    # Create balance record (restore stock)
                    DocumentItemBalance.objects.create(
                        document=refurbish_document,
                        document_item=refurbish_item,
                        product=doc_item.product,
                        qty=Decimal(doc_item.qty),
                        income_price=doc_item.income_price,
                        sale_price=doc_item.sale_price,
                        currency_rate=doc_item.currency_rate,
                        currency_rate_value=doc_item.currency_rate_value,
                        profit_as_percent=doc_item.profit_as_percent,
                        shop=doc_item.shop,
                        user=doc_item.user,
                    )
                doc_item.soft_delete()
            document.soft_delete()
        return Response({"message": "Document deleted successfully."}, status=status.HTTP_200_OK)


class BuyProductView(GenericAPIView):
    serializer_class = BuyProductSerializer

    def post(self, request, *args, **kwargs):
        user: User = request.user
        try:
            with transaction.atomic():
                payed_money = request.data.get('payed_money')
                un_payed_money = request.data.get('un_payed_money')
                note = request.data.get('note', None)
                supplier_id = request.data.get('supplier_id')

                supplier = Supplier.objects.get(id=supplier_id)
                first_part = ProductPart.objects.get(id=request.data.get("product_part_ids")[0])
                shop = first_part.shop

                latest = CurrencyRate.objects.order_by('-created_at').filter(
                    shop=first_part.shop
                ).first()
                converted_payed_money = payed_money
                converted_un_payed_money = un_payed_money

                if first_part.product.currency_type == CURRENCY_USD:
                    converted_payed_money = Convertor.to_decimal(payed_money) / latest.rate
                    converted_un_payed_money = Convertor.to_decimal(un_payed_money) / latest.rate

                # Create Document
                document_factory = DocumentFactory(
                    user=user, shop=shop,
                    doc_type='buy',
                    supplier=supplier,
                    payment_info_data=PaymentInfoData(
                        first_part=first_part, payed_money=converted_payed_money,
                        un_payed_money=converted_un_payed_money, note=note,
                        currency_type=first_part.product.currency_type
                    )
                )
                document = document_factory.create()

                # Create Debt Balance
                self.update_or_create_supplier_debt(first_part, supplier, converted_un_payed_money, request.user)

                # Process Product Parts
                self.process_product_parts(request, user, document, supplier)

            return Response({"message": "Product bought successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def process_product_parts(self, request, user, document, supplier):
        for item in request.data.get('product_part_ids'):
            product_part = ProductPart.objects.get(id=item)

            if product_part.income_price == 0:
                profit_percentage = 0
            else:
                profit_percentage = Calculator.percentage(
                    product_part.sale_price, product_part.income_price
                )

            document_item = DocumentItem.objects.create(
                document=document,
                product=product_part.product,
                qty=product_part.qty,
                profit_as_percent=Decimal(str(profit_percentage)),
                income_price=product_part.income_price,
                currency_rate=product_part.currency_rate if product_part.currency_rate else None,
                currency_rate_value=product_part.currency_rate.rate if product_part.currency_rate else Decimal('0.0'),
                shop=document.shop,
                user=user,
                sale_price=product_part.sale_price
            )
            document_item.save()

            product_balance: DocumentItemBalance = DocumentItemBalance.objects.filter(
                product=product_part.product,
                shop=document.shop,
                currency_rate=product_part.currency_rate,
                income_price=product_part.income_price
            ).select_for_update().first()
            print(f"Product Balance: {product_balance}")
            if product_balance:
                product_balance.qty += Decimal(str(product_part.qty))
                product_balance.save()
            else:
                balance = DocumentItemBalance.objects.create(
                    qty=product_part.qty, income_price=product_part.income_price,
                    currency_rate=product_part.currency_rate if product_part.currency_rate else None,
                    currency_rate_value=product_part.currency_rate.rate if product_part.currency_rate else Decimal(
                        '0.0'),
                    profit_as_percent=profit_percentage, document_item=document_item,
                    shop=document_item.shop, user=user,
                    document=document,
                    product=product_part.product,
                    sale_price=product_part.sale_price
                )
                balance.save()

            product_part.confirm(user, supplier)

    def update_or_create_supplier_debt(
            self, first_part: ProductPart, supplier: Supplier,
            un_payed_money, user
    ):
        latest = CurrencyRate.objects.order_by('-created_at').filter(
            shop=first_part.shop
        ).first()
        converted_currency = None
        try:
            supplier_debt_balance = SupplierDebtBalance.objects.get(
                supplier=supplier
            )

            if first_part.product.currency_type == CURRENCY_USD:
                converted_currency = Convertor.to_decimal(un_payed_money) * Convertor.to_decimal(latest.rate)
                # supplier_debt_balance.balance_usd += Convertor.to_decimal(un_payed_money)
                # SupplierTransaction.objects.create(
                #     shop=first_part.shop,
                #     balance=supplier_debt_balance, amount=un_payed_money, currency_type='usd',
                #     currency_rate=latest.rate, transaction_type='debt',
                #     supplier=supplier, created_by=user
                # )

            supplier_debt_balance.balance_uzs += Convertor.to_decimal(converted_currency)
            SupplierTransaction.objects.create(
                shop=first_part.shop,
                balance=supplier_debt_balance, amount=converted_currency, currency_type='uzs',
                currency_rate=Decimal('0.0'), transaction_type='debt',
                supplier=supplier, created_by=user
            )
            supplier_debt_balance.save()
        except SupplierDebtBalance.DoesNotExist:
            if first_part.product.currency_type == CURRENCY_USD:
                converted_currency = Convertor.to_decimal(un_payed_money) * Convertor.to_decimal(latest.rate)
                # balance = SupplierDebtBalance.objects.create(
                #     supplier=supplier,
                #     balance_usd=un_payed_money
                # )
                # SupplierTransaction.objects.create(
                #     shop=first_part.shop,
                #     balance=balance, amount=un_payed_money, currency_type='usd',
                #     currency_rate=latest.rate, transaction_type='debt',
                #     supplier=supplier, created_by=user
                # )

            balance = SupplierDebtBalance.objects.create(
                supplier=supplier,
                balance_uzs=converted_currency
            )
            SupplierTransaction.objects.create(
                shop=first_part.shop,
                balance=balance, amount=converted_currency, currency_type='uzs',
                currency_rate=Decimal('0.0'), transaction_type='debt',
                supplier=supplier, created_by=user
            )


class SellProductView(GenericAPIView):
    serializer_class = SellProductSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        products_data = request.data.get("products")
        discount = request.data.get("discount", 0.0)
        note = request.data.get("note", None)
        promo_code_id = request.data.get('promo_code', None)
        payment_method = request.data.get('payment_method')

        shop_id = None

        promo_code = None

        if promo_code_id:
            promo_code = PromoCode.objects.get(id=promo_code_id)

        if not products_data or not isinstance(products_data, list):
            return Response({"error": "Invalid or missing 'products' data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Get first product to determine shop
                first_item = products_data[0]
                product = Product.objects.get(id=first_item.get("product_id"))
                shop_id = product.shop.id

                document_factory = DocumentFactory(
                    user=user,
                    shop=product.shop,
                    doc_type='sell',
                    payment_detail_data=PaymentDetailData(
                        note=note,
                        payment_method=payment_method,
                        discount=Decimal(str(discount)),
                        promo_code=promo_code,
                        promo_code_value=Decimal(str(promo_code.value)) if promo_code is not None else Decimal("0.0")
                    )
                )

                document = document_factory.create()

                latest_currency = CurrencyRate.objects.filter(
                    shop=document.shop
                ).order_by('-created_at').first()
                if not latest_currency:
                    raise Exception("Currency rate not available.")

                for item in products_data:
                    product_id = item.get('product_id')
                    sell_qty = Decimal(str(item.get('qty')))  # ✅ Always ensure Decimal

                    if not product_id or sell_qty <= 0:
                        raise Exception("Each product must have valid 'product_id' and 'qty'.")

                    product = Product.objects.get(id=product_id)

                    # Get all balances for that product in that shop ordered FIFO
                    balances = DocumentItemBalance.objects.filter(
                        product=product,
                        shop=document.shop,
                        qty__gt=0
                    ).order_by('created_at')

                    total_available = sum(b.qty for b in balances)
                    if Decimal(total_available) < sell_qty:
                        raise Exception(f"Not enough stock for product {product.name}.")

                    remaining_qty = sell_qty

                    for balance in balances:
                        if remaining_qty <= 0:
                            break

                        deduct_qty = min(balance.qty, remaining_qty)

                        DocumentItem.objects.create(
                            document=document,
                            product=product,
                            currency_rate=latest_currency if product.currency_type == 'usd' else None,
                            currency_rate_value=latest_currency.rate if product.currency_type == 'usd' else Decimal(
                                '0.0'),
                            qty=deduct_qty,
                            income_price=balance.income_price,
                            profit_as_percent=balance.profit_as_percent,
                            shop=document.shop,
                            user=user,
                            sale_price=balance.sale_price
                        )

                        balance.qty -= deduct_qty
                        balance.save()

                        remaining_qty -= deduct_qty

                if shop_id is not None:
                    SalaryCalculatorService(request, shop_id).calculate_personal_salary()

            return Response({"message": "Product sold successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
