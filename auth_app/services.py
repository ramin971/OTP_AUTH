import random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from kavenegar import *
from .models import OTPCode, FailedAttempt



class OTPService:
    @staticmethod
    def generate_otp(phone, order):
        # Delete previous OTPs
        OTPCode.objects.filter(phone=phone).delete()

        # Generate new OTP
        # code = str(random.randint(100000, 999999)) don't support code that start 0 like (042...6)
        code = ''.join(random.choices('0123456789', k=6))
        expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        # print(f'###############code:{code}#############')
        
        otp = OTPCode.objects.create(
            phone=phone,
            code=code,
            expires_at=expires_at
        )
        
        # TODO: Integrate with SMS service (transaction.attomic)
        # send OTP via sms
        OTPService.send_sms(phone, code, order)
        
        return code
    

    @staticmethod
    def send_sms(phone_number, code, order):
        try:
            api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
            params = {
                'receptor': phone_number,
                'template': order,
                'token': code,
                'type': 'sms', #sms vs call
            }
            response = api.verify_lookup(params)
            # print(f'###{response}###')
            return response
        except APIException as e:
            decoded_error = e.args[0].decode('utf-8')
            raise ValidationError(f"Error sending SMS: {decoded_error}")
        except HTTPException as e:
            raise ValidationError(f"Error connecting to KAVENEGAR service: {str(e)}")


    @staticmethod
    def verify_otp(phone, code):
        otp = OTPCode.objects.filter(
            phone=phone,
            code=code,
            is_used=False,
            expires_at__gte=timezone.now()
        ).first()
        
        if otp:
            otp.is_used = True
            otp.save()
            return True
        return False
    

    @staticmethod
    def check_throttle(ip_address, phone=None, attempt_type='LOGIN'):
        # check faild-attempts-number
        one_hour_ago = timezone.now() - timedelta(hours=settings.ATTEMPTS_TIME_RANGE)

        if phone:
            phone_attempts = FailedAttempt.objects.filter(attempt_type=attempt_type,\
                                                          created_at__gte=one_hour_ago,\
                                                          phone=phone).count()
            if phone_attempts > settings.FAILED_ATTEMPTS_LIMIT:
                return False
            
        ip_attempts = FailedAttempt.objects.filter(
            ip_address=ip_address,
            attempt_type=attempt_type,
            created_at__gte=one_hour_ago
        ).count()
        if ip_attempts > settings.FAILED_ATTEMPTS_LIMIT:
            # AuthService.block_ip(ip, 'LOGIN')
            return False
        
        return True
    
    @staticmethod
    def record_failed_attempt(ip_address, phone=None, attempt_type='LOGIN'):
        FailedAttempt.objects.create(
            ip_address=ip_address,
            phone=phone,
            attempt_type=attempt_type
        )

    # @staticmethod
    # def block_ip(ip, block_type):
    #     blocked_until = timezone.now() + timedelta(hours=settings.BLOCK_TIME_HOURS)
    #     IPBlock.objects.create(
    #         ip_address=ip,
    #         block_type=block_type,
    #         blocked_until=blocked_until
    #     )
    #     cache_key = f'blocked_ip_{ip}_{block_type}'
    #     cache.set(cache_key, True, timeout=settings.BLOCK_TIME_HOURS * 3600)
