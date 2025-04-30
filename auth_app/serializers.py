import re
from rest_framework import serializers
from .models import User


class PhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11)

    def validate_phone(self, value):
        # Simple phone number validation
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value

class LoginSerializer(PhoneNumberSerializer):
    password = serializers.CharField(write_only=True)

class RegisterSerializer(LoginSerializer):
    
    def create(self, validated_data):
        user = User.objects.create_user(
            phone=validated_data['phone'],
            password=validated_data['password']
        )
        return user

class VerifyOTPSerializer(PhoneNumberSerializer):
    code = serializers.CharField(min_length=6, max_length=6)

# class ResendOTPSerializer(PhoneNumberSerializer):
#     pass

# class CompleteProfileSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(
#         write_only=True,
#         required=False,
#         min_length=8,
#         style={'input_type': 'password'}
#     )
    
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'email', 'password']
#         extra_kwargs = {
#             'first_name': {'required': True},
#             'last_name': {'required': True},
#             'email': {'required': True},
#         }


