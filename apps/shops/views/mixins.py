import datetime
from collections import defaultdict
from decimal import Decimal

from django.db import transaction as django_transaction
from django.db.models import Sum
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.cart.models import Cart
from apps.cart.serializers import CartSerializer
from apps.customer_transaction.models import CustomerTransaction
from apps.customer_transaction.serializers import CustomerTransactionSerializer
from apps.document.models import DocumentItemBalance
from apps.document.utils.calculator import Calculator
from apps.notifications.models import Notification, NotificationType
from apps.orders.models import Order, OrderStatus
from apps.orders.serializers import OrderSerializer
from apps.products.models import Product, ProductGroup
from apps.products.serializers import CreateProductsGroupSerializer, ProductPositionSerializer, ProductSerializer, \
    SeparateProductsSerializer, ProductSerializerForUser
from apps.promocodes.serializers import PromocodeSerializer
from apps.role_manager.serializer import RoleSerializer
from apps.shops.models import ShopBalanceTransaction, Shop, ShopBalance
from apps.shops.serializers import ChangeExchangeRateSerializer, ShopContactSerializer, ShopSerializer, \
    ShopMemberSerializer
from apps.shops.serializers import ShopTransactionSerializer
from apps.supplier.models import Supplier, SupplierDebtBalance, SupplierTransaction
from apps.supplier.serializers import DebtPaymentHistorySerializer, SupplierSerializer
from common.filters import ProductFilter
from common.serializers import EmptyBodySerializer
from utils.convertor import Convertor


class SubscriptionActionMixin:
    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(detail=True, methods=["POST"], parser_classes=[JSONParser])
    def join(self, request, *args, **kwargs):
        """Foydalanuvchini do'konga a'zo qilish."""
        shop = self.get_object()
        user = request.user

        if user not in shop.members.all():
            shop.members.add(user)
            return Response({"message": "Do'konga muvaffaqiyatli a'zo bo'ldingiz"})
        else:
            return Response({"message": "Siz allaqachon ushbu do'kon a'zosisiz"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(detail=True, methods=["POST"], parser_classes=[JSONParser])
    def leave(self, request, *args, **kwargs):
        """Foydalanuvchini do'kondan chiqarish."""
        shop = self.get_object()
        user = request.user

        if user in shop.members.all():
            shop.members.remove(user)

            return Response({"message": "Do'kondan muvaffaqiyatli chiqdingiz"})
        else:
            return Response({"message": "Siz do'kon a'zosi emassiz"}, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={200: ShopSerializer(many=True)})
    @action(methods=["GET"], detail=False, url_path="my-subscriptions")
    def my_subscriptions(self, request):
        """Foydalanuvchi a'zo bo'lgan barcha do'konlarni olish."""
        user = request.user
        shops = self.get_queryset().filter(members=user)

        page = self.paginate_queryset(shops)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(shops, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: ShopSerializer(many=True)})
    @action(methods=["GET"], detail=False, serializer_class=ShopSerializer)
    def owned(self, request):
        """Foydalanuvchiga tegishli do'konlarni olish."""
        user = request.user

        shops = Shop.objects.filter(roles__user=user).distinct()

        page = self.paginate_queryset(shops)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(shops, many=True, context={"user": user})
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: ShopMemberSerializer(many=True)})
    @action(methods=["GET"], detail=True, serializer_class=ShopMemberSerializer)
    def members(self, request, pk=None):
        """Do'konning foydalanuvchilar ro'yhatini olish."""

        shop = self.get_object()
        Through = Shop.members.through

        qs = Through.objects.filter(shop=shop).exclude(user=request.user)
        data = ShopMemberSerializer(qs, many=True, context={"request": request}).data

        return Response(data)


class ProductGroupActionMixin:
    @action(detail=True, methods=["GET"], url_path="product-groups")
    def products_groups(self, request, *args, **kwargs):
        shop = self.get_object()

        # Remove notification for new products for this user and shop
        Notification.objects.filter(
            type=NotificationType.NEW_PRODUCT, user=request.user, shop=shop
        ).delete()

        # Fetch products and their related data
        products = Product.objects.prefetch_related("favorited_by").select_related(
            "category", "group"
        ).filter(shop=shop)

        # Fetch balance products
        balance_products = DocumentItemBalance.objects.filter(
            deleted_at=None, shop=shop
        ).select_related("product", "product__category", "product__group")

        # Category map initialization
        category_map = defaultdict(lambda: {
            "id": None,
            "category": "",
            "total_profit": 0.0,
            "total_cost": 0.0,
            "groups": [],
        })

        # Calculate total profit and cost per category
        for balance in balance_products:
            product = balance.product
            category = product.category
            if not category:
                continue

            category_id = category.id
            category_name = category.name

            if category_id not in category_map:
                category_map[category_id]["id"] = category_id
                category_map[category_id]["category"] = category_name
                category_map[category_id]["groups"] = []
                category_map[category_id]["total_profit"] = 0.0
                category_map[category_id]["total_cost"] = 0.0

            try:
                qty = float(balance.qty or 1)
                cost = float(balance.income_price or 0)

                # Profit calculation
                if product.currency_type == 'usd':
                    profit = Calculator.profit_in_uzs(
                        balance.sale_price, balance.income_price, balance.currency_rate.rate
                    )
                else:
                    profit = Calculator.profit(
                        balance.sale_price, balance.income_price
                    )

                # Add to totals
                total_cost = cost * qty * float(
                    balance.currency_rate_value) if product.currency_type == 'usd' else cost * qty
                category_map[category_id]["total_profit"] += float(
                    profit) * qty
                category_map[category_id]["total_cost"] += total_cost

            except Exception as e:
                print(
                    f"[Profit/Cost Error] Product ID: {product.id}, Error: {e}")

        # Fill product groups
        for product in products:
            category = product.category
            group = product.group
            if not category:
                continue

            category_id = category.id
            group_id = str(group.id) if group else None

            if category_id not in category_map:
                category_map[category_id]["id"] = category_id
                category_map[category_id]["category"] = category.name
                category_map[category_id]["groups"] = []
                category_map[category_id]["total_profit"] = 0.0
                category_map[category_id]["total_cost"] = 0.0

            group_found = False
            for grp in category_map[category_id]["groups"]:
                if grp["id"] == group_id:
                    grp["products"].append(product)
                    group_found = True
                    break

            if not group_found:
                category_map[category_id]["groups"].append({
                    "id": group_id,
                    "products": [product],
                })

        # Serialize result
        result = []
        for cat in category_map.values():
            for grp in cat["groups"]:
                grp["products"] = ProductSerializer(
                    grp["products"], many=True, context={"request": request}
                ).data
            cat["total_profit"] = round(cat["total_profit"], 2)
            cat["total_cost"] = round(cat["total_cost"], 2)
            result.append(cat)

        return Response(result, status=status.HTTP_200_OK)

    @action(["PUT"], detail=True, url_path="merge-products", serializer_class=CreateProductsGroupSerializer,
            parser_classes=[JSONParser])
    def merge_products(self, request, *args, **kwargs):
        shop = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        target_product = serializer.validated_data.get("target_product")
        group = serializer.validated_data.get("group")

        if target_product:
            group = target_product.group

            if not group:
                group = ProductGroup.objects.create(shop=shop)

                target_product.group = group
                target_product.save()

        product.group = group
        product.save()

        return Response({"detail": f"Product {product.id} added to group {group.id}"})

    @action(["PUT"], detail=True, url_path="separate-product", serializer_class=SeparateProductsSerializer,
            parser_classes=[JSONParser])
    def separate_product(self, request, *args, **kwargs):
        self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]

        if product.group:
            product.group = None
            product.save()

        return Response({"detail": f"Product {product.id} separated from its group"})


class ShoppingCartActionMixin:
    @action(["GET"], detail=True, url_path="shopping-cart", serializer_class=CartSerializer,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        user = request.user
        shop = self.get_object()

        cart, created = (
            Cart.objects.select_related(
                "customer",
                "shop",
                "promocode",
            )
            .prefetch_related(
                "items__product__parts",
                "items__product__images",
                "items__product__category",
                "items__product__favorited_by",
                "shop__members",
                "shop__contacts",
                "shop__categories",
                "promocode__items",
                "promocode__items__product",
            )
            .get_or_create(customer=user, shop=shop)
        )

        serializer = self.get_serializer(cart)

        return Response(serializer.data)


class OrderActionMixin:
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY,
                              description="Sahifa raqami", type=openapi.TYPE_INTEGER),
            openapi.Parameter("page_size", openapi.IN_QUERY, description="Har bir sahifadagi elementlar soni",
                              type=openapi.TYPE_INTEGER),
        ],
        responses={200: ProductSerializer(many=True)},
    )
    @action(["GET"], detail=True, serializer_class=OrderSerializer)
    def order(self, request, *args, **kwargs):
        shop = self.get_object()
        user = request.user

        queryset = Order.objects.select_related("shop", "customer", "admin").prefetch_related("items").filter(shop=shop,
                                                                                                              customer=user).order_by(
            "-created_at")

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductActionsMixin:
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY,
                              description="Sahifa raqami", type=openapi.TYPE_INTEGER),
            openapi.Parameter("page_size", openapi.IN_QUERY, description="Har bir sahifadagi elementlar soni",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter("search", openapi.IN_QUERY,
                              description="Search across name, description, barcode, category name",
                              type=openapi.TYPE_STRING),
            openapi.Parameter("name", openapi.IN_QUERY,
                              description="Filter by product name", type=openapi.TYPE_STRING),
            openapi.Parameter("barcode", openapi.IN_QUERY,
                              description="Filter by barcode", type=openapi.TYPE_STRING),
            openapi.Parameter("description", openapi.IN_QUERY, description="Filter by description",
                              type=openapi.TYPE_STRING),
            openapi.Parameter("category", openapi.IN_QUERY, description="Filter by category ID",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter("is_selected", openapi.IN_QUERY, description="Filter by is selected",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter("is_active", openapi.IN_QUERY, description="Filter by is active",
                              type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: ProductSerializer(many=True)},
    )
    @action(detail=True, methods=["GET"])
    def products(self, request, *args, **kwargs):
        """Do'kondagi barcha mahsulotlarni olish."""
        queryset = self.get_object().products.prefetch_related(
            "images", "parts").order_by("position_number")
        filtered_qs = ProductFilter(request.GET, queryset=queryset).qs
        page = self.paginate_queryset(filtered_qs)

        if page is not None:
            serializer = ProductSerializer(
                page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductSerializer(
            filtered_qs, many=True, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY,
                              description="Sahifa raqami", type=openapi.TYPE_INTEGER),
            openapi.Parameter("page_size", openapi.IN_QUERY, description="Har bir sahifadagi elementlar soni",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter("search", openapi.IN_QUERY,
                              description="Search across name, description, barcode, category name",
                              type=openapi.TYPE_STRING),
            openapi.Parameter("name", openapi.IN_QUERY,
                              description="Filter by product name", type=openapi.TYPE_STRING),
            openapi.Parameter("barcode", openapi.IN_QUERY,
                              description="Filter by barcode", type=openapi.TYPE_STRING),
            openapi.Parameter("description", openapi.IN_QUERY, description="Filter by description",
                              type=openapi.TYPE_STRING),
            openapi.Parameter("category", openapi.IN_QUERY, description="Filter by category ID",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter("is_selected", openapi.IN_QUERY, description="Filter by is selected",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter("is_active", openapi.IN_QUERY, description="Filter by is active",
                              type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: ProductSerializer(many=True)},
    )
    @action(detail=True, methods=["GET"], url_path="products-groups-user")
    def products_groups_user(self, request, *args, **kwargs):
        """Do'kondagi barcha mahsulotlarni guruhlar bo'yicha olish."""
        queryset = self.get_object().products.prefetch_related(
            "images", "parts").order_by("position_number")
        products = ProductFilter(request.GET, queryset=queryset).qs

        category_map = defaultdict(
            lambda: {"id": None, "category": "", "groups": []})

        for product in products:
            category = product.category
            group = product.group
            category_id = category.id
            category_name = category.name
            group_id = str(group.id) if group else None

            if category_id not in category_map:
                category_map[category_id]["id"] = category_id
                category_map[category_id]["category"] = category_name
                category_map[category_id]["groups"] = []

            found = False
            for grp in category_map[category_id]["groups"]:
                if grp["id"] == group_id:
                    grp["products"].append(product)
                    found = True
                    break
            if not found:
                category_map[category_id]["groups"].append(
                    {"id": group_id, "products": [product]})

        result = []
        for cat in category_map.values():
            for grp in cat["groups"]:
                grp["products"] = ProductSerializerForUser(grp["products"], many=True,
                                                           context={"request": request}).data
            result.append(cat)

        return Response(result, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ProductPositionSerializer(many=True))
    @action(methods=["PATCH"], detail=True, url_path="update-products-order",
            serializer_class=ProductPositionSerializer, parser_classes=[JSONParser])
    def update_products_order(self, request, *args, **kwargs):
        """Mahsulotlar tartibini yangilash."""
        shop = self.get_object()
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        positions = {pair["product_id"]: pair["position_number"]
                     for pair in serializer.validated_data}
        products = Product.objects.filter(pk__in=positions.keys(), shop=shop)

        if not products.exists():
            raise ValidationError(
                {"message": "Ma'lumotlar bazasida keltirilgan mahsulotlar topilmadi."})

        for product in products:
            product.position_number = positions.get(product.id)

        Product.objects.bulk_update(products, ["position_number"])
        return Response({"message": "Positions updated successfully"}, status=status.HTTP_200_OK)


class ContactActionsMixin:
    @action(methods=["GET"], detail=True, serializer_class=ShopContactSerializer)
    def contacts(self, request, *args, **kwargs):
        """Do'kondagi barcha kontaktlarni olish."""
        shop = self.get_object()
        contacts = shop.contacts.all()
        serializer = ShopContactSerializer(
            contacts, many=True, context={"request": request})
        return Response(serializer.data)


class AdminActionsMixin:
    @action(methods=["GET"], detail=True, serializer_class=RoleSerializer)
    def admins(self, request, *args, **kwargs):
        """Do'kon adminlar ro'yxatini olish."""
        shop = self.get_object()

        # get all roles in this shop
        roles = shop.roles.all()

        # check if current user is the shop owner
        if shop.roles.filter(user=request.user, role="owner").exists():
            # exclude owner's role from the result
            roles = roles.exclude(user=request.user)

        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)


class ExchangeRateActionsMixin:
    @swagger_auto_schema(request_body=ChangeExchangeRateSerializer)
    @action(methods=["PUT"], detail=True, url_path="change-exchange-rate",
            serializer_class=ChangeExchangeRateSerializer, parser_classes=[JSONParser])
    def change_exchange_rate(self, request, *args, **kwargs):
        """Do'konning valyuta kursini yangilash."""
        self.check_permissions(request)
        shop = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rate = Decimal(serializer.validated_data["rate"])
        old_rate = Decimal(shop.usd_exchange_rate)
        products = list(shop.products.filter(is_active=True))

        for product in products:
            product.sale_price = product.sale_price / old_rate * rate

        Product.objects.bulk_update(products, ["sale_price"])
        shop.usd_exchange_rate = rate
        shop.save(update_fields=["usd_exchange_rate"])
        return Response({"message": "Exchange rate and product prices updated successfully"}, status=status.HTTP_200_OK)


class PromocodeActionsMixin:
    @action(methods=["GET"], detail=True, serializer_class=PromocodeSerializer)
    def promocodes(self, request, *args, **kwargs):
        """Do'kondagi promokodlarni olish."""
        promocodes = self.get_object().promocodes.all()
        serializer = self.get_serializer(promocodes, many=True)
        return Response(serializer.data)


class ShopHistoryActionsMixin:
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, description="start_date (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter("end_date", openapi.IN_QUERY, description="end_date (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING),
        ]
    )
    @action(methods=["GET"], detail=True, url_path="history/orders")
    def order_history(self, request, *args, **kwargs):
        """Do'kon tarixini olish."""
        shop = self.get_object()

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        orders = Order.objects.filter(
            shop=shop).select_related("admin", "customer")

        if start_date:
            try:
                start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
                orders = orders.filter(created_at__date__gte=start_date_dt)
            except ValueError:
                return Response({"error": "start_date format must be YYYY-MM-DD"}, status=400)

        if end_date:
            try:
                end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
                orders = orders.filter(created_at__date__lte=end_date_dt)
            except ValueError:
                return Response({"error": "end_date format must be YYYY-MM-DD"}, status=400)

        stats_orders = orders.filter(
            status__in=[OrderStatus.ACCEPTED, OrderStatus.COMPLETED])

        # statistics = stats_orders.aggregate(
        #     total_price=Sum("total_price"),
        #     discount=Sum("discount"),
        #     agreed_price=Sum("agreed_price"),
        #     debt=Sum("debt"),
        #     total_profit=Sum("profit"),
        # )

        orders = OrderSerializer(
            instance=orders, many=True, context={"request": request})

        return Response({"orders": orders.data, })

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, description="start_date (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter("end_date", openapi.IN_QUERY, description="end_date (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING),
        ]
    )
    @action(methods=["GET"], detail=True, url_path="history/transactions")
    def transaction_history(self, request, *args, **kwargs):
        shop = self.get_object()

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        supplier_transactions = SupplierTransaction.objects.order_by('-created_at').filter(
            shop=shop
        )
        customer_transaction = CustomerTransaction.objects.order_by('-created_at').filter(
            shop=shop
        )

        if start_date:
            try:
                start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
                supplier_transactions = supplier_transactions.filter(date__gte=start_date_dt)
                customer_transaction = customer_transaction.filter(date__gte=start_date_dt)
            except ValueError:
                return Response({"error": "start_date format must be YYYY-MM-DD"}, status=400)

        if end_date:
            try:
                end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
                supplier_transactions = supplier_transactions.filter(date__lte=end_date_dt)
                customer_transaction = customer_transaction.filter(date__gte=start_date_dt)
            except ValueError:
                return Response({"error": "end_date format must be YYYY-MM-DD"}, status=400)

        profit_spent = supplier_transactions.filter(transaction_type="profit").aggregate(
            total=Sum("amount"))["total"] or 0
        cash_spent = supplier_transactions.filter(transaction_type="cash").aggregate(
            total=Sum("amount"))["total"] or 0
        cash_and_profit_spent = \
            supplier_transactions.filter(transaction_type="cash_and_profit").aggregate(total=Sum("amount"))[
                "total"] or 0
        current_cash_total = \
            supplier_transactions.filter(transaction_type__in=["cash", "cash_and_profit"]).aggregate(
                total=Sum("amount"))[
                "total"] or 0

        statistics = {
            "cash_spent": cash_spent,
            "profit_spent": profit_spent,
            "cash_and_profit_spent": cash_and_profit_spent,
            "current_cash_total": current_cash_total,
        }

        serialized_supplier = DebtPaymentHistorySerializer(supplier_transactions, many=True).data
        serialized_customer = CustomerTransactionSerializer(customer_transaction, many=True).data

        for transaction in serialized_customer:
            transaction['type'] = 'customer_transaction'
        for transaction in serialized_supplier:
            transaction['type'] = 'supplier_transaction'

        return Response(
            {
                "transactions": serialized_supplier + serialized_customer,
                "statistics": statistics
            }
        )


class ShopBalanceMixin:
    @swagger_auto_schema(request_body=ShopTransactionSerializer)
    @action(methods=['POST'], url_path="calculate-balance", detail=False)
    def calculate_balance(self, request, *args, **kwargs):
        transaction = self.create_transaction(request)
        kind = request.data.get('kind')
        shop = Shop.objects.get(id=request.data.get('shop'))
        amount = request.data.get('amount')
        balance: ShopBalance = shop.balance
        supplier_id = request.data.get('supplier', None)

        with django_transaction.atomic():
            if kind == 'profit':
                balance.profit = balance.profit + Convertor.to_decimal(amount)
            if kind == 'cash_income':
                balance.cash = balance.cash + Convertor.to_decimal(amount)
            if kind == 'cash_profit':
                balance.profit = balance.profit + Convertor.to_decimal(amount)
                balance.cash = balance.cash + Convertor.to_decimal(amount)

            if kind == 'loss':
                balance.profit = balance.profit - Convertor.to_decimal(amount)
                self.calculate_supplier_debt(supplier_id, amount)

            if kind == 'cash_outcome':
                balance.cash = balance.cash - Convertor.to_decimal(amount)
                self.calculate_supplier_debt(supplier_id, amount)

            if kind == 'cash_loss':
                balance.cash = balance.cash - Convertor.to_decimal(amount)
                balance.profit = balance.profit - Convertor.to_decimal(amount)
                self.calculate_supplier_debt(supplier_id, amount)

            balance.save()

        serializer = ShopTransactionSerializer(transaction, many=False)

        return Response(
            serializer.data,
        )

    @staticmethod
    def calculate_supplier_debt(supplier_id, amount):
        supplier = None
        if supplier_id:
            supplier = Supplier.objects.get(id=supplier_id)

        if supplier:
            debt_balance: SupplierDebtBalance = supplier.debt_balance
            debt_balance.balance_uzs = debt_balance.balance_uzs - \
                                       Convertor.to_decimal(amount)
            SupplierTransaction.objects.create(
                supplier=supplier, balance=debt_balance, amount=amount,
                currency_type='uzs', currency_rate=Decimal('0.0'), created_by=supplier.created_by
            )

    @staticmethod
    def create_transaction(request: Request) -> ShopBalanceTransaction:
        kind = request.data.get('kind')
        amount = request.data.get('amount')
        note = request.data.get('note')
        shop_id = request.data.get('shop')
        shop = Shop.objects.get(id=shop_id)
        transaction = ShopBalanceTransaction.objects.create(
            created_by=request.user,
            amount=amount, note=note, shop=shop, kind=kind
        )

        print("[+] Transaction was created")
        return transaction


class SupplierFilterMixin:
    supplier_serializer_class = SupplierSerializer

    @action(methods=["GET"], detail=True, url_path="suppliers")
    def suppliers(self, request, pk=None, *args, **kwargs):
        shop_id = pk
        queryset = Supplier.objects.filter(shops__id=shop_id)

        name = request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        page = self.paginate_queryset(queryset)
        serializer_class = getattr(self, "supplier_serializer_class", None)
        if not serializer_class:
            raise ValueError("Supplier serializer class not defined")

        if page is not None:
            serializer = serializer_class(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True, context={"request": request})
        return Response(serializer.data)
