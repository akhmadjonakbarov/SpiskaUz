from decimal import Decimal

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.currency_rate.models import CurrencyRate
from apps.debt.models import Debt
from apps.document.factories.document_factory import DocumentFactory, PaymentInfoData, PaymentDetailData
from apps.document.models import Document, DocumentItem, DocumentItemBalance
from apps.document.serializers import DocumentSerializer, BuyProductSerializer, SellProductSerializer
from apps.document.utils.calculator import Calculator
from apps.product_part.models import ProductPart
from apps.products.models import Product
from apps.promocodes.models import PromoCode
from apps.supplier.models import SupplierDebtBalance
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
                type=openapi.TYPE_STRING
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
                currency_type = request.data.get('currency_type', None)
                supplier = Supplier.objects.get(id=supplier_id)
                first_part = ProductPart.objects.get(id=request.data.get("product_part_ids")[0])
                shop = first_part.shop

                if currency_type is None:
                    return Response(
                        data={
                            'detail': 'Please select currency type. CurrencyType might be usd or uzs'
                        }
                    )

                # Create Document
                document_factory = DocumentFactory(
                    user=user, shop=shop,
                    doc_type='buy',
                    payment_info_data=PaymentInfoData(
                        first_part=first_part, payed_money=payed_money, un_payed_money=un_payed_money, note=note,
                        currency_type=currency_type
                    )
                )
                document = document_factory.create()

                # Create Debt Balance
                self.update_or_create_supplier_debt(first_part, supplier, un_payed_money)

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
            self, currency_type: str, supplier: Supplier, un_payed_money
    ):

        try:
            supplier_debt_balance = SupplierDebtBalance.objects.get(
                supplier=supplier
            )

            if currency_type == CURRENCY_USD:
                supplier_debt_balance.balance_usd += Convertor.to_decimal(un_payed_money)
            else:
                supplier_debt_balance.balance_usd += Convertor.to_decimal(un_payed_money)
            supplier_debt_balance.save()
        except SupplierDebtBalance.DoesNotExist:
            if currency_type == CURRENCY_USD:
                SupplierDebtBalance.objects.create(
                    supplier=supplier,
                    balance_usd=un_payed_money
                )
            else:
                SupplierDebtBalance.objects.create(
                    supplier=supplier,
                    balance_uzs=un_payed_money
                )


class SellProductView(GenericAPIView):
    serializer_class = SellProductSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        client_id = None
        paid_money = None
        user = request.user
        products_data = request.data.get("products")
        discount = request.data.get("discount", 0.0)
        note = request.data.get("note", None)
        promo_code_id = request.data.get('promo_code', None)
        payment_method = request.data.get('payment_method')
        debt = request.data.get('debt', None)
        if debt is not None:
            client_id = debt['client']
            paid_money = debt['paid_money']

        promo_code = None
        client = None

        if client_id:
            client = User.objects.get(id=client_id)

        if promo_code_id:
            promo_code = PromoCode.objects.get(id=promo_code_id)

        if not products_data or not isinstance(products_data, list):
            return Response({"error": "Invalid or missing 'products' data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Get first product to determine shop
                first_item = products_data[0]
                product = Product.objects.get(id=first_item.get("product_id"))

                document_factory = DocumentFactory(
                    user=user,
                    shop=product.shop,
                    doc_type='sell',
                    payment_detail_data=PaymentDetailData(
                        note=note,
                        payment_method=payment_method,
                        discount=Decimal(str(discount)),
                        promo_code=promo_code,
                        promo_code_value=Decimal(str(promo_code.value)) if promo_code else Decimal("0.0")
                    )
                )

                document = document_factory.create()
                if client:
                    Debt.objects.create(
                        created_by=request.user,
                        client=client,
                        paid_money=paid_money if float(paid_money) > 0 else Decimal('0.0'),
                        document=document,
                        shop=document.shop
                    )
                    print(f'[+] Debt was created for {client}')

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

            return Response({"message": "Product sold successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
