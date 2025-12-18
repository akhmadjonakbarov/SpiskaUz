from apps.admin_panel.models import SalaryBalance, PercentageTracker
from apps.document.models import Document, DocumentItem
from apps.role_manager.models import Role
from django.db.models import Prefetch


class CalculateSalaryService:
    def __init__(self, request, shop_id=None):
        self.request = request
        self.user = request.user
        self.shop_id = shop_id

        self.role = Role.objects.activate(user=self.user).first()
        self.salary_balance = None

    def get_or_create_balance(self):
        self.salary_balance, _ = SalaryBalance.actives.get_or_create(
            role=self.role
        )

    def calculate_salary_by_user(self):
        self.get_or_create_balance()

        documents = (
            Document.actives
            .filter(
                created_by=self.user,
                doc_type='sell',
            )
            .prefetch_related(
                Prefetch(
                    "document_items",
                    queryset=(
                        DocumentItem.actives
                        .select_related(
                            "product",  # if FK
                            # OR "variant__product"
                        )
                    )
                )
            )
        )

        total_salary = 0

        for document in documents:
            tracker, created = PercentageTracker.objects.get_or_create(
                document=document
            )

            if not created:
                continue
            document_items = (
                document.document_items.all().prefetch_related(
                    "product",
                )
            )
            for item in document_items:
                total_salary += item.outcome_price or 0

        self.salary_balance.amount += total_salary
        self.salary_balance.save(update_fields=["amount"])

        return total_salary
