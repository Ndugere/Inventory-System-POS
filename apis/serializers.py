from rest_framework import serializers
from django.contrib.auth.models import User
from . import models as db

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'password'
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'firstname',
            'lastname',
            'email',
        ]

class PasswordSerializer(serializers.Serializer):
    password2 = serializers.CharField()
    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'password2',
        ]
    