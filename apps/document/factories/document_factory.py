from django.db import transaction

from apps.document.models import Document, PaymentDetail, PaymentInfo
from apps.supplier.models import DebtPurchase


class PaymentDetailData:
    def __init__(
            self, payment_method, discount, promo_code, promo_code_value, note,
    ):
        self.payment_method = payment_method
        self.discount = discount
        self.promo_code = promo_code
        self.promo_code_value = promo_code_value
        self.note = note


class PaymentInfoData:
    def __init__(self, first_part, payed_money, un_payed_money, note, currency_type):
        self.first_part = first_part
        self.payed_money = payed_money
        self.un_payed_money = un_payed_money
        self.note = note
        self.currency_type = currency_type


class DocumentFactory:
    def __init__(
            self,
            user, shop, doc_type, supplier=None,
            payment_info_data: PaymentInfoData = None,
            payment_detail_data: PaymentDetailData = None
    ):
        self.user = user
        self.shop = shop
        self.doc_type = doc_type
        self.supplier = supplier
        self.payment_info_data = payment_info_data
        self.payment_detail_data = payment_detail_data

    def create(self) -> Document:
        with transaction.atomic():
            document = Document.objects.create(
                user=self.user,
                shop=self.shop,
                doc_type=self.doc_type,
                supplier=self.supplier
            )

            if self.payment_detail_data:
                self._create_payment_detail(document)

            if self.doc_type == 'buy' and self.payment_info_data:
                self._create_payment_info(document)

            return document

    def _create_payment_detail(self, document: Document):
        PaymentDetail.objects.create(
            document=document,
            note=self.payment_detail_data.note,
            payment_method=self.payment_detail_data.payment_method,
            discount=self.payment_detail_data.discount,
            promo_code_value=self.payment_detail_data.promo_code_value
        )

    def _create_payment_info(
            self, document: Document
    ):
        PaymentInfo.objects.create(
            user=self.user, document=document,
            note=self.payment_info_data.note, payed_money=self.payment_info_data.payed_money,
            un_payed_money=self.payment_info_data.un_payed_money, shop=document.shop,
            currency_type=self.payment_info_data.currency_type
        )
        if self.payment_info_data.un_payed_money > 0:
            DebtPurchase.objects.create(
                created_by=self.user, document=document,
                supplier=document.supplier, total_money=self.payment_info_data.un_payed_money,
                remained_money=self.payment_info_data.un_payed_money,
                currency_type=self.payment_info_data.currency_type
            )
