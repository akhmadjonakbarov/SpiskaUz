from django.utils.dateparse import parse_date
from apps.document.models import Document
from apps.shops.models import Shop
from apps.shops.models import ShopBalanceTransaction


class DocumentSelector:

    @staticmethod
    def filter_documents(
            *,
            shop: Shop,
            doc_type: str,
            from_date: str | None = None,
            to_date: str | None = None,
    ):
        qs = (
            Document.actives
            .filter(
                shop=shop,
                doc_type=doc_type,
            )
            .select_related("payment_detail")
            .prefetch_related("document_items", "document_items__product")
            .order_by("-created_at")
        )

        if from_date:
            qs = qs.filter(created_at__date__gte=parse_date(from_date))

        if to_date:
            qs = qs.filter(created_at__date__lte=parse_date(to_date))

        return qs


class ShopBalanceTransactionSelector:
    @staticmethod
    def filter_shop_balance_transactions(
            *,
            shop: Shop,
            from_date: str | None = None,
            to_date: str | None = None,
    ):
        qs = (
            ShopBalanceTransaction.actives.filter(
                shop=shop, )
        )
        if from_date:
            qs = qs.filter(created_at__date__gte=parse_date(from_date))
        if to_date:
            qs = qs.filter(created_at__date__lte=parse_date(to_date))
        return qs
