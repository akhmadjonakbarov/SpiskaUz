import factory

from apps.document.factories.document_factory import DocumentFactory
from apps.document.models import Document


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    doc_type = 'sell'
