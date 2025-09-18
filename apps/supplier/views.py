from decimal import Decimal

from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db import transaction, IntegrityError
from rest_framework.exceptions import ValidationError
from utils.convertor import Convertor
from .serializers import SupplierSerializer, CreateSupplierSerializer, PayDebtSerializer, DebtPaymentHistorySerializer
from .models import Supplier, SupplierDebtBalance, Transaction
from apps.currency_rate.models import CurrencyRate
from apps.shops.models import Shop


class SupplierViewSet(ModelViewSet):
    queryset = Supplier.objects.all().filter(
        deleted_at=None
    )
    serializer_class = SupplierSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateSupplierSerializer

        return SupplierSerializer

    def create(self, request, *args, **kwargs):
        phone_number = request.data.get("phone_number")
        name = request.data.get("name")
        shop_id = request.data.get("shop")

        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            raise ValidationError({"shop": "Invalid shop id"})

        try:
            with transaction.atomic():
                supplier, created = Supplier.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={"created_by": request.user, "name": name},
                )
                supplier.shops.add(shop)
        except IntegrityError:
            raise ValidationError({"phone_number": "This phone number already exists."})

        return Response(
            {
                "id": supplier.id,
                "name": supplier.name,
                "phone_number": supplier.phone_number,
                "shops": [s.id for s in supplier.shops.all()],
                "created": created,
            }
        )

    def destroy(self, request, *args, **kwargs):
        supplier = self.get_object()
        supplier.soft_delete()
        return Response(
            data={
                'detail': 'Supplier was deleted'
            }, status=200
        )


class SupplierDebtPayView(GenericAPIView):
    serializer_class = PayDebtSerializer
    queryset = Supplier.objects.all()
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, id):
        supplier = self.queryset.get(id=id)
        balance_debt: SupplierDebtBalance = SupplierDebtBalance.objects.get(
            supplier=supplier
        )
        is_debt_available = balance_debt.balance_uzs == 0 and balance_debt.balance_usd == 0
        if is_debt_available:
            return Response(
                data={
                    'detail': 'Debt does not exist'
                }
            )

        try:
            with transaction.atomic():
                currency_type = request.data.get('currency_type')
                amount = request.data.get('amount')

                if currency_type == 'usd':
                    balance_debt.balance_usd = Convertor.to_decimal(balance_debt.balance_usd) - Convertor.to_decimal(
                        amount
                    )
                else:
                    balance_debt.balance_uzs = Convertor.to_decimal(balance_debt.balance_uzs) - Convertor.to_decimal(
                        amount
                    )
                balance_debt.save()
                currency_rate = None
                if currency_type == 'usd':
                    currency_rate = CurrencyRate.objects.filter(user=request.user).order_by(
                        '-created_at'
                    ).first()

                Transaction.objects.create(
                    balance=balance_debt,
                    created_by=request.user,
                    currency_type=currency_type,
                    currency_rate=Decimal(currency_rate.rate) if currency_rate is not None else Decimal('0.0'),
                    amount=amount,
                    supplier=supplier
                )
            return Response(
                data={
                    'detail': 'Debt has been paid successfully'
                }, status=status.HTTP_200_OK
            )

        except Supplier.DoesNotExist:
            raise ValueError("Object does not exist")


class SupplierDebtPaymentHistoryView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Transaction.objects.all()
    serializer_class = DebtPaymentHistorySerializer

    def get_queryset(self):
        supplier_id = self.kwargs['pk']
        return self.queryset.filter(
            supplier_id=supplier_id
        )
