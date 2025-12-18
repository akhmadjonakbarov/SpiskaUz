import random

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP, User


# class AuthTestCase(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#
#         self.test_phone = "+998333932580"
#         self.test_otp = random.randint(100000, 999999)
#
#         self.user, _ = User.objects.get_or_create(
#             phone="+998333932580",
#             defaults={
#                 "first_name": "Abdurazzoq",
#                 "last_name": "Abdurazzoq",
#             },
#         )
#
#         self.otp = OTP.objects.create(user=self.user, code=self.test_otp)
#         self.refresh = RefreshToken.for_user(self.user)
#
#     def test_send_otp(self):
#         url = reverse("user-send_otp")
#         data = {"phone": self.test_phone}
#
#         response = self.client.post(url, data, format="json")
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("detail", response.data)
#
#     def test_verify_otp(self):
#         url = reverse("user-verify_otp")
#         data = {"phone": self.test_phone, "otp": str(self.test_otp)}
#
#         response = self.client.post(url, data, format="json")
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("refresh", response.data)
#         self.assertIn("access", response.data)
#         self.assertIn("user", response.data)
#
#     def test_get_user(self):
#         url = reverse("user-whoami")
#
#         self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.refresh.access_token))
#
#         response = self.client.get(url, format="json")
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("first_name", response.data)
#         self.assertIn("last_name", response.data)
#         self.client.credentials()
