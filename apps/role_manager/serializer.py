from rest_framework import serializers
from .models import RoleUser


class RoleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleUser
        fields = ('role', 'user', 'shop')


class CreateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleUser
        fields = ('role', 'user', 'shop')


