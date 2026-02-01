from apps.admin_panel.models import SalaryBalance, PercentageTracker
from apps.document.models import Document, DocumentItem
from apps.role_manager.models import Role

from decimal import Decimal
from django.db import transaction
from django.db.models import Prefetch


class SalaryCalculatorService:
    def __init__(self, request, shop_id=None):
        self.request = request
        self.user = request.user
        self.shop_id = shop_id

        self.role = Role.actives.filter(user=self.user).first()
        self.salary_balance = None

    def get_or_create_balance(self):
        self.salary_balance, _ = SalaryBalance.actives.get_or_create(
            role=self.role
        )

    def calculate_personal_salary(self):

        with transaction.atomic():
            self.get_or_create_balance()

            documents = (
                Document.actives
                .filter(
                    user=self.user,
                    doc_type='sell',
                )
                .select_related("payment_detail")
                .prefetch_related(
                    Prefetch(
                        "document_items",
                        queryset=DocumentItem.actives.select_related("product")
                    )
                )
            )

            total_salary = Decimal("0.0")

            for document in documents:
                tracker, created = PercentageTracker.objects.get_or_create(
                    document=document
                )

                if not created:
                    continue

                total_price = document.get_total_outcome_price_uzs()

                salary_price = (
                        Decimal(self.role.admin_commission_percent)
                        / Decimal("100.00")
                        * total_price
                )
                print(f"[+] Salary: {salary_price}")

                total_salary += salary_price

            print(f"[+] Total Salary: {total_salary}")
            self.salary_balance.personal_salary += total_salary
            self.salary_balance.save(update_fields=["personal_salary"])

            return total_salary

    def calculate_global_salary(self):
        pass
