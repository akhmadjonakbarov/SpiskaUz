from rest_framework import serializers
from .models import Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('role', 'user', 'shop')


class CreateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            'role', 'user', 'shop', 'salary'
        )
