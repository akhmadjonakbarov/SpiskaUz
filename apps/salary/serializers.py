from rest_framework import serializers

from apps.salary.models import SalaryTransaction


class SalaryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryTransaction
        fields = "__all__"
