from rest_framework.serializers import ModelSerializer

from apps.customer_transaction.models import CustomerTransaction


class CustomerTransactionSerializer(ModelSerializer):
    class Meta:
        model = CustomerTransaction
        fields = "__all__"
