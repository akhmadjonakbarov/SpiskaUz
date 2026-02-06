from collections import defaultdict
from decimal import Decimal

from django.db import transaction as django_transaction, transaction
from django.db.models import OuterRef, Exists
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.cart.models import Cart
from apps.cart.serializers import CartSerializer
from apps.document.models import DocumentItemBalance, Document
from apps.document.serializers import DocumentSerializerForStatistic
from apps.document.utils.calculator import Calculator
from apps.notifications.models import Notification, NotificationType
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from apps.products.models import Product, ProductGroup
from apps.products.serializers import (
    CreateProductsGroupSerializer, ProductPositionSerializer,
    ProductSerializer, SeparateProductsSerializer, ProductSerializerForUser
)
from apps.promocodes.serializers import PromocodeSerializer
from apps.role_manager.models import Role
from apps.role_manager.serializer import RoleSerializer
from apps.shops.filters import OrderFilter, DocumentFilter, ShopBalanceTransactionFilter
from apps.shops.models import ShopBalanceTransaction, Shop, ShopBalance
from apps.shops.serializers import ChangeExchangeRateSerializer, ShopContactSerializer, ShopSerializer, \
    ShopMemberSerializer, ShopBalanceCalculateSerializer
from apps.shops.serializers import ShopTransactionSerializer
from apps.supplier.models import Supplier, SupplierDebtBalance, SupplierTransaction
from apps.supplier.serializers import SupplierSerializer
from common.filters import ProductFilter
from common.serializers import EmptyBodySerializer
from utils.convertor import Convertor


class SubscriptionActionMixin:
    @swagger_auto_schema(request_body=EmptyBodySerializer)
    @action(detail=True, methods=["POST"], parser_classes=[JSONParser])
    def join(self, request, *args, **kwargs):
        """Foydalanuvchini do'konga a'zo qilish."""
        shop = Shop.actives.get(id=kwargs['pk'])
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
        shop = Shop.actives.get(id=kwargs.get("pk"))
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

    @swagger_auto_schema(
        operation_summary="List shop orders",
        operation_description="Get paginated list of orders for a shop with filtering",
        manual_parameters=[
            openapi.Parameter(
                "is_admin",
                openapi.IN_QUERY,
                description="Filter via IsAdmin field",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: OrderSerializer(many=True),
        },
    )
    @action(methods=["GET"], detail=True, serializer_class=ShopMemberSerializer)
    def members(self, request, pk=None):
        shop = Shop.objects.get(id=pk)
        Through = Shop.members.through

        admin_subquery = Role.objects.filter(
            user=OuterRef("user"),
            shop=OuterRef("shop"),
        )

        qs = (
            Through.objects
            .filter(shop=shop)
            .exclude(user=request.user)
            .annotate(is_admin=Exists(admin_subquery))
        )

        # 🔥 filtering by is_admin
        is_admin = request.query_params.get("is_admin")
        if is_admin is not None:
            qs = qs.filter(is_admin=is_admin.lower() == "true")

        serializer = ShopMemberSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class ProductGroupActionMixin:
    @action(detail=True, methods=["GET"], url_path="product-groups")
    def products_groups(self, request, *args, **kwargs):

        shop = Shop.objects.get(id=kwargs.get("pk"))

        # Remove notification for new products for this user and shop
        Notification.objects.filter(
            type=NotificationType.NEW_PRODUCT, user=request.user, shop=shop
        ).delete()

        # Fetch products and their related data
        products = Product.objects.prefetch_related("favorited_by").select_related(
            "category", "group"
        ).filter(shop_id=kwargs.get("pk"))

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
        shop = Shop.actives.get(id=kwargs.get("pk"))

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
        shop = Shop.actives.get(id=kwargs.get("pk"))

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
        operation_summary="List shop orders",
        operation_description="Get paginated list of orders for a shop with filtering",
        manual_parameters=[
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Order status (new, processing, done, canceled)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "exclude",
                openapi.IN_QUERY,
                description="Order status (new, processing, done, canceled)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "customer",
                openapi.IN_QUERY,
                description="Customer ID",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Items per page",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                name="from_date",
                in_=openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                name="to_date",
                in_=openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
        ],
        responses={
            200: OrderSerializer(many=True),
        },
    )
    @action(
        methods=["GET"],
        detail=True,
        serializer_class=OrderSerializer,
        url_path="orders",
    )
    def orders(self, request, pk):
        exclude = request.query_params.get("exclude")
        queryset = (
            Order.objects
            .select_related("shop", "customer", "admin")
            .prefetch_related("items")
            .filter(shop_id=pk)
            .order_by("-created_at")
        )
        if exclude is not None:
            queryset = (
                Order.objects
                .select_related("shop", "customer", "admin")
                .prefetch_related("items").exclude(status=exclude)
                .filter(shop_id=pk)
                .order_by("-created_at")
            )

        filtered_qs = OrderFilter(request.GET, queryset=queryset).qs

        page = self.paginate_queryset(filtered_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_qs, many=True)
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

        shop_id = kwargs.get("pk")
        """Do'kondagi barcha mahsulotlarni olish."""
        shop = Shop.objects.get(pk=shop_id)
        queryset = shop.products.prefetch_related(
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
        queryset = Shop.actives.get(id=kwargs.get("pk")).products.prefetch_related(
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
        shop = Shop.actives.get(id=kwargs.get("pk"))
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
        shop = Shop.actives.get(id=kwargs.get("pk"))
        contacts = shop.contacts.all()
        serializer = ShopContactSerializer(
            contacts, many=True, context={"request": request})
        return Response(serializer.data)


class AdminActionsMixin:
    @action(methods=["GET"], detail=True, serializer_class=RoleSerializer)
    def admins(self, request, *args, **kwargs):
        """Do'kon adminlar ro'yxatini olish."""
        shop = Shop.actives.get(id=kwargs.get("pk"))

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
        shop = Shop.actives.get(id=kwargs.get("pk"))
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
        promocodes = Shop.actives.get(id=kwargs.get("pk")).promocodes.all()
        serializer = self.get_serializer(promocodes, many=True)
        return Response(serializer.data)


class ShopBalanceMixin:
    @swagger_auto_schema(request_body=ShopBalanceCalculateSerializer)
    @action(
        methods=["POST"],
        url_path="calculate-balance",
        detail=False,
    )
    def calculate_balance(self, request: Request):

        input_serializer = ShopBalanceCalculateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data
        print(data)

        kind = data["kind"]
        amount = Convertor.to_decimal(data["amount"])
        shop: Shop = data["shop"]
        supplier = data.get("supplier")

        balance: ShopBalance = shop.balance

        with django_transaction.atomic():
            # ✅ Create transaction record
            transaction = ShopBalanceTransaction.objects.create(
                created_by=request.user,
                amount=amount,
                note=data.get("note"),
                shop=shop,
                kind=kind,
            )

            # ✅ Balance calculations
            if kind == "profit":
                pass
                # balance.profit += amount

            elif kind == "cash_income":
                pass
                # balance.cash += amount

            elif kind == "cash_profit":
                pass
                # balance.profit += amount
                # balance.cash += amount

            elif kind == "loss":
                # balance.profit -= amount
                self.calculate_supplier_debt(supplier, amount)

            elif kind == "cash_outcome":
                # balance.cash -= amount
                self.calculate_supplier_debt(supplier, amount)

            elif kind == "cash_loss":
                # balance.cash -= amount
                # balance.profit -= amount
                self.calculate_supplier_debt(supplier, amount)

            balance.save()

        output_serializer = ShopTransactionSerializer(transaction)
        return Response(output_serializer.data)

    # ------------------------------------------------------------------

    @staticmethod
    def calculate_supplier_debt(supplier: Supplier | None, amount: Decimal):
        if not supplier:
            return

        with django_transaction.atomic():
            debt_balance: SupplierDebtBalance = supplier.debt_balance
            debt_balance.balance_uzs -= Convertor.to_decimal(amount)
            debt_balance.save()

            SupplierTransaction.objects.create(
                supplier=supplier,
                balance=debt_balance,
                amount=amount,
                currency_type="uzs",
                currency_rate=Decimal("0.0"),
                created_by=supplier.created_by,
                transaction_type="debt",
            )


class ShopBalanceTransactionMixin:
    transaction_serializer_class = ShopTransactionSerializer

    @swagger_auto_schema(
        operation_summary="List shop balance transactions",
        operation_description=(
                "Returns a paginated list of balance transactions for a specific shop. "
                "Supports filtering by amount and date range."
        ),
        manual_parameters=[
            openapi.Parameter(
                name="kind",
                in_=openapi.IN_QUERY,
                description="Filter by transaction kind",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                name="transaction_type",
                in_=openapi.IN_QUERY,
                description="Filter by transaction type (income, outcome)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                name="from_date",
                in_=openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                name="to_date",
                in_=openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                name="page",
                in_=openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                name="page_size",
                in_=openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: ShopTransactionSerializer(many=True),
        },
    )
    @action(
        methods=["GET"],
        detail=True,
        url_path="shop-balance-transactions",
    )
    def shop_balance_transactions(self, request, pk=None):
        serializer_class = self.transaction_serializer_class

        queryset = (
            ShopBalanceTransaction.actives
            .filter(shop_id=pk)
            .select_related("shop", "created_by")
            .order_by("-created_at")
        )

        # Apply filters correctly
        filterset = ShopBalanceTransactionFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


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


class DocumentMixin:
    document_serializer_class = DocumentSerializerForStatistic

    @swagger_auto_schema(
        operation_summary="List Shop Documents",
        operation_description="Get paginated list of orders for a shop with filtering",
        manual_parameters=[
            openapi.Parameter(
                "doc_type",
                openapi.IN_QUERY,
                description="Document status (sell, buy)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "supplier",
                openapi.IN_QUERY,
                description="Customer ID",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                name="from_date",
                in_=openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                name="to_date",
                in_=openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Items per page",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "user_id",
                openapi.IN_QUERY,
                description="Admin ID",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={200: OrderSerializer(many=True)},
    )
    @action(methods=["GET"], detail=True, url_path="documents")
    def documents(self, request, *args, **kwargs):
        shop = Shop.actives.get(id=kwargs.get("pk"))

        queryset = Document.objects.filter(shop=shop)
        filtered_qs = DocumentFilter(request.GET, queryset=queryset).qs

        page = self.paginate_queryset(filtered_qs)
        if page is not None:
            serializer = self.document_serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.document_serializer_class(filtered_qs, many=True)
        return Response(serializer.data)
