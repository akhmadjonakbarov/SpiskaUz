from django.http import JsonResponse
from django.utils import timezone

from apps.daily_session.models import DailySession


def add_api(url) -> str:
    return f'/api/v1/{url}'


SKIP_PATHS = (
    '/api/v1/auth',
    add_api('units'),
    add_api('shop'),
    add_api('day'),
    '/swagger',
    '/admin',
    add_api('currency-rates'),
    add_api('supplier'),
    '/api/v1/advertisement-category/',
    '/api/v1/product/favorite/',
    '/api/v1/advertisement/favorite/',
    '/api/v1/cart-item/',
    add_api('role-manager'),
    '/api/v1/product/upload-image/'
)


class IsDayOpenMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        print('[+] IsDayOpenMiddleware initialized')

    def __call__(self, request):
        if request.path.startswith(SKIP_PATHS):
            return self.get_response(request)
        shop_id = request.headers.get('ShopId')  # Or your header name
        if not shop_id:
            return JsonResponse({'detail': 'Missing shop ID'}, status=400)

        today = timezone.localdate()
        daily_session = DailySession.objects.filter(
            shop_id=shop_id,
            date=today
        ).first()

        if not daily_session:
            return JsonResponse({'detail': 'No session found for today'}, status=404)

        if not daily_session.is_open:
            return JsonResponse({'detail': 'Shop is closed'}, status=403)

        return self.get_response(request)
