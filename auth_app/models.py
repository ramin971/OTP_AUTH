from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.password_validation import validate_password as validate_pass 
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator,MinLengthValidator
from django.conf import settings



class CustomUserManager(BaseUserManager):

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone field must be set')
        # validate_pass(password)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('SuperUser must be set is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('SuperUser must be set is_superuser=True')
        # validate_pass(password)

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    phone = models.CharField(max_length=11, unique=True,\
                             validators=[RegexValidator(regex='^09\d{9}$'\
                                                        ,message='phone number invalid',\
                                                        code='invalid_phone')])
    is_verified = models.BooleanField(default=False)
    username = None
    USERNAME_FIELD = 'phone'
    # REQUIRED_FIELDS = ['email']
    objects = CustomUserManager()
    
    def __str__(self):
        return self.phone

class OTPCode(models.Model):
    phone = models.CharField(max_length=11,\
                             validators=[RegexValidator(regex='^09\d{9}$'\
                                                        ,message='phone number invalid',\
                                                        code='invalid_phone')])
    code = models.CharField(max_length=6, validators=[MinLengthValidator(6)])
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    # set 5min expire time
    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        super().save(*args, **kwargs)

class FailedAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    phone = models.CharField(max_length=11,validators=[RegexValidator(regex='^09\d{9}$')],\
                              null=True, blank=True)
    attempt_type = models.CharField(max_length=20)  # in ['LOGIN','OTP'] 
    created_at = models.DateTimeField(auto_now_add=True)

# class IPBlock(models.Model):
#     ip_address = models.GenericIPAddressField()
#     *block_type = models.CharField(max_length=10, choices=[
#         ('LOGIN', 'Login'),
#         ('REGISTER', 'Register'),
#         ('OTP', 'OTP Verification')
#     ])
#     blocked_until = models.DateTimeField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     *class Meta:
#         indexes = [
#             models.Index(fields=['ip_address', 'block_type']),
#         ]