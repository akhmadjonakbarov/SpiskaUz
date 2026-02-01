from decimal import Decimal
from django.test import TestCase

from apps.admin_panel.models import SalaryBalance
from apps.admin_panel.services import SalaryCalculatorService
from apps.document.models import DocumentItem, Document, PaymentDetail
from apps.products.models import Product
from apps.role_manager.models import Role
from apps.shops.models import Shop
from apps.users.models import User


class CalculateSalaryServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="123456798")

        self.shop = Shop.objects.create(
            name="Test Shop",
            description="Test",
            address="Tashkent",
            latitude="0",
            longitude="0",
            image="test.jpg"
        )

        self.role = Role.objects.create(
            user=self.user,
            shop=self.shop,
            total_commission_percent=Decimal("10")
        )

        self.product = Product.objects.create(
            name="Test Product",
            currency_type="UZS",
            sale_price=Decimal("10000"),
            discount=Decimal("0.0"),
            user=self.user,
            shop=self.shop,
            barcode="55465456asdasa"
        )

    def _mock_request(self, user):
        class DummyRequest:
            def __init__(self, user):
                self.user = user
        return DummyRequest(user)

    def test_salary_calculated_for_shop(self):
        document = Document.objects.create(
            user=self.user,
            shop=self.shop,
            doc_type="sell",
        )

        DocumentItem.objects.create(
            document=document,
            product=self.product,
            qty=2,
            sale_price=Decimal("10000"),
            income_price=Decimal("8000"),
            currency_rate_value=Decimal("1"),
            user=self.user,
            shop=self.shop
        )

        service = SalaryCalculatorService(
            request=self._mock_request(self.user),
            shop_id=self.shop.id
        )

        total_salary = service.calculate_personal_salary()

        self.assertEqual(total_salary, Decimal("2000"))
        self.assertEqual(
            SalaryBalance.objects.get(role=self.role).personal_salary,
            Decimal("2000")
        )

    def test_other_shop_documents_are_ignored(self):
        other_shop = Shop.objects.create(
            name="Other Shop",
            description="Other",
            address="Samarkand",
            latitude="0",
            longitude="0",
            image="test.jpg"
        )

        Document.objects.create(
            user=self.user,
            shop=other_shop,
            doc_type="sell",
        )

        service = SalaryCalculatorService(
            request=self._mock_request(self.user),
            shop_id=self.shop.id
        )

        self.assertEqual(service.calculate_personal_salary(), Decimal("0"))

    def test_discount_price_used_for_shop(self):
        document = Document.objects.create(
            user=self.user,
            shop=self.shop,
            doc_type="sell",
        )

        DocumentItem.objects.create(
            document=document,
            product=self.product,
            qty=10,
            sale_price=Decimal("10000"),
            income_price=Decimal("8000"),
            currency_rate_value=Decimal("1"),
            user=self.user,
            shop=self.shop
        )

        PaymentDetail.objects.create(
            document=document,
            discount=Decimal("50000"),
            payment_method="cash"
        )

        service = SalaryCalculatorService(
            request=self._mock_request(self.user),
            shop_id=self.shop.id
        )

        self.assertEqual(service.calculate_personal_salary(), Decimal("5000"))
