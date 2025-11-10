from rest_framework import serializers

from apps.salary.models import SalaryTransaction


class SalaryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryTransaction
        exclude = ('deleted_at',)
