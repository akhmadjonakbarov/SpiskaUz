from datetime import timedelta

from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import OTP, User, now

from .serializers import RefreshTokenSerializer, SendOTPSerializer, UserSerializer, VerifyOTPSerializer, \
    SimpleUserSerializer


class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        permissions.AllowAny,
    ]

    @action(["POST"], detail=False, url_path="send-otp", url_name="send_otp")
    def send_otp(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        user, _ = User.objects.get_or_create(phone=phone)

        otp_code = "555555"

        otp = OTP.objects.filter(user=user).first()

        # ⏱️ Rate limit: 20 seconds
        if otp and (now() - otp.created_at) < timedelta(seconds=2):
            return Response(
                {"detail": "OTP allaqachon yuborilgan. Iltimos, 20 soniya kuting."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Create or update OTP AFTER check
        OTP.objects.update_or_create(
            user=user,
            defaults={
                "code": otp_code,
                "created_at": now()
            }
        )

        # send_otp_code(phone, otp_code)

        return Response(
            {"detail": "OTP muvaffaqiyatli yuborildi."},
            status=status.HTTP_200_OK
        )

    @action(["POST"], detail=False, url_path="verify-otp", url_name="verify_otp")
    def verify_otp(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["otp"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"detail": "Telefon raqami yoki OTP kodi noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = OTP.objects.filter(user=user).first()

        if not otp:
            return Response(
                {"detail": "OTP topilmadi. Iltimos, qaytadan yuboring."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.is_expired():
            otp.delete()
            return Response(
                {"detail": "OTP kodi muddati tugagan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.code != code:
            return Response(
                {"detail": "OTP kodi noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ OTP correct → consume it
        otp.delete()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": SimpleUserSerializer(
                    instance=user,
                    context={"request": request}
                ).data
            },
            status=status.HTTP_200_OK
        )

    @action(["POST"], detail=False, url_path="refresh-token", url_name="refresh_token")
    def refresh_token(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh_token"]

        try:
            token = RefreshToken(refresh_token)
            access_token = token.access_token

            return Response({"access": str(access_token)}, status=status.HTTP_200_OK)

        except Exception:
            return Response({"detail": "Noto'g'ri yoki muddati tugagan token."}, status=status.HTTP_400_BAD_REQUEST)

    @action(["POST"], detail=False, url_path="sign-up", url_name="sign_up",
            permission_classes=[permissions.IsAuthenticated],
            parser_classes=[parsers.FormParser, parsers.MultiPartParser])
    def sign_up(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, instance=request.user)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(["GET"], detail=False, url_path="whoami", url_name="whoami",
            permission_classes=[permissions.IsAuthenticated])
    def whoami(self, request, *args, **kwargs):
        return Response(self.get_serializer(instance=request.user).data)

    def get_serializer_class(self):
        serializers = {"send_otp": SendOTPSerializer, "verify_otp": VerifyOTPSerializer,
                       "refresh_token": RefreshTokenSerializer, "sign_up": UserSerializer}
        return serializers.get(self.action, self.serializer_class)


def well_known(request):
    return JsonResponse(
        [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": "com.spiskauz.spiskauz_app",
                    "sha256_cert_fingerprints": [
                        "0B:20:FF:18:D8:2D:B6:FC:E9:7F:E1:09:FC:D1:85:48:96:F7:8C:E5:77:F9:75:D6:13:EA:91:FC:9D:AB:31:D2"],
                },
            }
        ],
        safe=False,
    )


def logout_page(request):
    logout(request)

    return redirect(request.GET.get("next", "/"))
