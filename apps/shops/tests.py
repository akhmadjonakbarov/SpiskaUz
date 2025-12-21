from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.document.models import Document
from apps.shops.factories import ShopFactory
from apps.shops.models import Shop
from apps.users.models import User


class DocumentMixinTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="999921684",
        )
        self.client.force_authenticate(user=self.user)

        self.shop = ShopFactory()
        # Active documents
        self.doc1 = Document.objects.create(
            shop_id=self.shop.id,
            name="Doc 1",

        )
        self.doc2 = Document.objects.create(
            shop_id=self.shop.id,
            name="Doc 2",
            is_active=True
        )

        # Inactive document (should not appear)
        self.doc3 = Document.objects.create(
            shop_id=self.shop.id,
            name="Doc 3",
            is_active=False
        )

        self.url = reverse(
            "shop-documents",  # adjust to your router name
            kwargs={"pk": self.shop.id}
        )

    def test_documents_returns_only_active_documents(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        returned_names = [doc["name"] for doc in response.data]
        self.assertIn("Doc 1", returned_names)
        self.assertIn("Doc 2", returned_names)
        self.assertNotIn("Doc 3", returned_names)

    def test_documents_filtering(self):
        response = self.client.get(self.url, {"name": "Doc 1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Doc 1")

    def test_documents_pagination(self):
        # Force pagination by creating extra docs
        for i in range(10):
            Document.objects.create(
                shop_id=self.shop.id,
                name=f"Extra Doc {i}",
                is_active=True
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertGreater(response.data["count"], len(response.data["results"]))

    def test_documents_invalid_shop_returns_empty(self):
        url = reverse(
            "shop-documents",
            kwargs={"pk": 9999}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
