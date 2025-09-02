import os
from datetime import timedelta
from pathlib import Path

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from environs import Env

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = env.bool("DEBUG", default=True)
TESTING = env.bool("TESTING", default=False)
SECRET_KEY = env.str("SECRET_KEY")
OTP_EMAIL = env.str("OTP_EMAIL")
OTP_PASSWORD = env.str("OTP_PASSWORD")

ALLOWED_HOSTS = ["*"]

DJANGO_APPS = [
    # Unfold
    "unfold",
    "unfold.contrib.guardian",
    "unfold.contrib.import_export",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework_simplejwt",
    "rest_framework",
    "import_export",
    "django_filters",
    "drf_yasg",
    "guardian",
    "django_cleanup.apps.CleanupConfig",
]

LOCAL_APPS = [
    "apps.advertisements",
    "apps.cart",
    "apps.cash",
    "apps.debt",
    "apps.notifications",
    "apps.orders",
    "apps.products",
    "apps.promocodes",
    "apps.shops.apps.ShopsConfig",
    "apps.transactions",
    "apps.users",
    'apps.base',
    'apps.currency_rate',
    'apps.unit',
    'apps.document',
    'apps.product_part',
    'apps.store',
    'apps.supplier',
    'apps.daily_session',
    'apps.role_manager',
    'apps.statistics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

UNFOLD = {
    "SITE_TITLE": "Spiska Uz",
    "SITE_HEADER": "Spiska Uz Admin",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Admin Dashboard",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
            {
                "title": _("Users and Access"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("OTP Codes"),
                        "icon": "password",
                        "link": reverse_lazy("admin:users_otp_changelist"),
                    },
                ],
            },
            {
                "title": _("Shop & Product Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Shops"),
                        "icon": "store",
                        "link": reverse_lazy("admin:shops_shop_changelist"),
                    },
                    {
                        "title": _("Products"),
                        "icon": "package",
                        "link": reverse_lazy("admin:products_product_changelist"),
                    },
                    {
                        "title": _("Product Groups"),
                        "icon": "layers",
                        "link": reverse_lazy("admin:products_productgroup_changelist"),
                    },
                ],
            },
            {
                "title": _("Document & Document Items"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Document"),
                        "icon": "store",
                        "link": reverse_lazy("admin:document_document_changelist"),
                    },
                    {
                        "title": _("DocumentItem"),
                        "icon": "package",
                        "link": reverse_lazy("admin:document_documentitem_changelist"),
                    },
                    {
                        "title": _("DocumentItemBalance"),
                        "icon": "layers",
                        "link": reverse_lazy("admin:document_documentitembalance_changelist"),
                    },
                ],
            },
            {
                "title": _("Supplier & Debts"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Supplier"),
                        "icon": "store",
                        "link": reverse_lazy("admin:supplier_supplier_changelist"),
                    },
                    {
                        "title": _("SupplierDebtBalance"),
                        "icon": "package",
                        "link": reverse_lazy("admin:supplier_supplierdebtbalance_changelist"),
                    },
                    {
                        "title": _("DebtPaymentHistory"),
                        "icon": "layers",
                        "link": reverse_lazy("admin:supplier_debtpaymenthistory_changelist"),
                    },
                ],
            },
            {
                "title": _("Order Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Orders"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:orders_order_changelist"),
                    },
                    {
                        "title": _("Order Items"),
                        "icon": "list",
                        "link": reverse_lazy("admin:orders_orderitem_changelist"),
                    },
                    {
                        "title": _("Shopping Cart"),
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:cart_cart_changelist"),
                    },
                ],
            },
            {
                "title": _("Reports and Notifications"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Reports"),
                        "icon": "flag",
                        "link": reverse_lazy("admin:products_report_changelist"),
                    },
                    {
                        "title": _("Report Options"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:products_reportoption_changelist"),
                    },
                    {
                        "title": _("Notifications"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:notifications_notification_changelist"),
                    },
                ],
            },
            {
                "title": _("Promotions"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Promocodes"),
                        "icon": "tag",
                        "link": reverse_lazy("admin:promocodes_promocode_changelist"),
                    },
                    {
                        "title": _("Promocode Usages"),
                        "icon": "toggle_on",
                        "link": reverse_lazy("admin:promocodes_promocodeusage_changelist"),
                    },
                ],
            },
            {
                "title": _("Financial Operations"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Cash History"),
                        "icon": "credit_card",
                        "link": reverse_lazy("admin:cash_cashhistory_changelist"),
                    },
                    {
                        "title": _("Cash History Items"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:cash_cashhistoryitem_changelist"),
                    },
                    {
                        "title": _("Debt Payments"),
                        "icon": "credit_card",
                        "link": reverse_lazy("admin:debt_debtpayment_changelist"),
                    },
                    {
                        "title": _("Debt Conversions"),
                        "icon": "currency_exchange",
                        "link": reverse_lazy("admin:debt_debtconversion_changelist"),
                    },
                ],
            },
            {
                "title": _("Advertisements"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Advertisement Categories"),
                        "icon": "folder",
                        "link": reverse_lazy("admin:advertisements_advertisementcategory_changelist"),
                    },
                    {
                        "title": _("Advertisements"),
                        "icon": "sell",
                        "link": reverse_lazy("admin:advertisements_advertisement_changelist"),
                    },
                ],
            },
            {
                "title": _("System & Logs"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("API Logs"),
                        "icon": "terminal",
                        "link": reverse_lazy("admin:drf_api_logger_apilogsmodel_changelist"),
                    },
                ],
            },
        ],
    },
    "THEME": "light",
    "TABS": [
        {
            "models": [
                "app_label.model_name_in_lowercase",
            ],
            "items": [
                {
                    "title": _("Spiska Uz"),
                    "link": reverse_lazy("admin:users_otp_changelist"),
                    # "permission": "sample_app.permission_callback",
                },
            ],
        },
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Basic": {
            "type": "basic",
        },
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        },
    },
    "LOGOUT_URL": "/api/v1/auth/logout/",
    "LOGIN_URL": "/api/v1/auth/login/",
    "PERSIST_AUTH": True,
    "DOC_EXPANSION": "none",
    "DEEP_LINKING": True,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    # "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("uz", "Uzbek"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # ✅ MUST be a valid path

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Optional, for uploaded files

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

if DEBUG:
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE = MIDDLEWARE + ["silk.middleware.SilkyMiddleware"]
    SILKY_PYTHON_PROFILER = True
    SILKY_META = True

else:
    SILKY_ENABLED = False

# Logger

INSTALLED_APPS += ["drf_api_logger"]
MIDDLEWARE += ["drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware"]

DRF_API_LOGGER_DATABASE = True
