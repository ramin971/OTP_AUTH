import re
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password as validate_pass 
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

class RegisterSerializer(PhoneNumberSerializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self,value):
        validate_pass(value)
        return value
    
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

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','phone','is_verified','first_name','last_name'] 
        read_only_fields = ['id','is_verified','phone']



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True , write_only=True)
    new_password = serializers.CharField(required=True , write_only=True)

    def validate_old_password(self,value):
        user = self.context['user']
        if not user.check_password(value):
            raise serializers.ValidationError('Your old password was entered incorrectly.')
        return value
    
    def validate_new_password(self,value):
        validate_pass(value)
        return value
    
    def save(self, **kwargs):
        user = self.context['user']
        password = self.validated_data['new_password']
        user.set_password(password)
        user.save()
        return user