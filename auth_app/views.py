from rest_framework import status,mixins,viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect , ensure_csrf_cookie
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.conf import settings
from ipware import get_client_ip
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    # OpenApiParameter
    )
from .paginations import CustomPagination
from .services import OTPService
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    VerifyOTPSerializer,
    UserSerializer,
    ChangePasswordSerializer
    )
from .throttles import RegisterRateThrottle, LoginRateThrottle, OTPRateThrottle
from .models import User

@ensure_csrf_cookie
def get_csrf_token(request):
    return Response({'detail': 'CSRF cookie set'},status=status.HTTP_200_OK)

class RegisterAPIView(APIView):
    throttle_classes = [RegisterRateThrottle]
    @extend_schema(
        tags=['OTP'],
        summary="ثبت‌نام کاربر جدید",
        description="""
        مرحله اول ثبت‌نام: ارسال کد OTP به شماره موبایل.
        پس از 3 درخواست ناموفق از یک IP، برای 1 ساعت مسدود می‌شود.
        """,
        request=RegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=RegisterSerializer,
                description='کد OTP با موفقیت ارسال شد'
            ),
            400: OpenApiResponse(
                response=RegisterSerializer,
                description='شماره موبایل قبلا ثبت شده است'
            ),
            429: OpenApiResponse(
                response=RegisterSerializer,
                description='تعداد درخواست‌ها بیش از حد مجاز'
            )
        },
        examples=[
            OpenApiExample(
                'درخواست موفق',
                value={'phone': '09123456789', 'password': 'MySecurePassword123'},
                status_codes=['200']
            ),
            OpenApiExample(
                'شماره تکراری',
                value={'phone': '09123456789', 'password': 'MySecurePassword123'},
                status_codes=['400']
            ),
        ]
    )
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        phone = serializer.validated_data['phone']
        # ip = request.META.get('REMOTE_ADDR')
        client_ip, _ = get_client_ip(request)
        
        if not OTPService.check_throttle(client_ip, phone, attempt_type='LOGIN'):
            return Response(
                {'error': f'Too many attempts. Try again after {settings.ATTEMPTS_TIME_RANGE} hour.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        # if AuthService.is_ip_blocked(ip, 'REGISTER'):
        #     return Response(
        #         {'error': 'Too many registration attempts. Try again later.'},
        #         status=status.HTTP_429_TOO_MANY_REQUESTS
        #     )
        
        order = 'auth-register'
        # Generate and send OTP
        OTPService.generate_otp(phone,order)
        # print(f'###############code:{code}#############')

        return Response({
            'message': 'User registered. OTP sent successfully',
            'phone': phone
        }, status=status.HTTP_201_CREATED)



class LoginAPIView(APIView):
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        tags=['OTP'],
        summary="ورود کاربر",
        description="""
        احراز هویت کاربر با شماره موبایل و رمز عبور.
        پس از 3 تلاش ناموفق، کاربر برای 1 ساعت مسدود می‌شود.
        """,
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=LoginSerializer,
                description='احراز هویت موفق با توکن‌های JWT'
            ),
            400: OpenApiResponse(
                response=LoginSerializer,
                description='ورودی نامعتبر یا کاربر وجود ندارد'
            ),
            429: OpenApiResponse(
                response=LoginSerializer,
                description='تعداد درخواست‌ها بیش از حد مجاز'
            )
        },
        examples=[
            OpenApiExample(
                'درخواست موفق',
                value={'phone': '09123456789', 'password': 'MySecurePassword123'},
                status_codes=['200']
            ),
            OpenApiExample(
                'رمز عبور نامعتبر',
                value={'phone': '09123456789', 'password': 'wrongpass'},
                status_codes=['400']
            ),
        ],
        # parameters=[
        #     OpenApiParameter(
        #         name='X-Forwarded-For',
        #         type=str,
        #         location=OpenApiParameter.HEADER,
        #         description='آی‌پی کاربر برای بررسی محدودیت درخواست'
        #     )
        # ]
    )

    # @method_decorator(csrf_protect)  لازم نداره چون تغییری در یوزر و احراز هویت ایجاد نمیکنه
    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        password = serializer.validated_data['password']

        # ip = request.META.get('REMOTE_ADDR')
        client_ip, _ = get_client_ip(request)
        
        if not OTPService.check_throttle(client_ip, phone, attempt_type='LOGIN'):
            return Response(
                {'error': f'Too many attempts. Try again after {settings.ATTEMPTS_TIME_RANGE} hour.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        # if AuthService.is_ip_blocked(ip, 'LOGIN'):
        #     return Response(
        #         {'error': 'Too many failed attempts. Try again later.'},
        #         status=status.HTTP_429_TOO_MANY_REQUESTS
        #     )
        
        user = authenticate(request, phone=phone, password=password)
        
        if user is not None:
            order = 'auth-login'
            # Generate and send OTP
            OTPService.generate_otp(phone, order)
            # print(f'########{code}########')

            return Response(
                {'message': 'OTP sent to your phone'},
                status=status.HTTP_200_OK)

        else:
            if not User.objects.filter(phone=phone).exists():
                OTPService.record_failed_attempt(client_ip, attempt_type='LOGIN')
                return Response(
                    {'error': 'User does not exist. Please register.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            OTPService.record_failed_attempt(client_ip, phone, attempt_type='LOGIN')
            
            return Response(
                {'error': 'Invalid phone or password'},
                status=status.HTTP_400_BAD_REQUEST
            )




class OTPVerificationView(APIView):
    throttle_classes = [OTPRateThrottle]
    @extend_schema(
        tags=['OTP'],
        summary="تأیید کد OTP",
        description="""
        تأیید کد یکبار مصرف ارسال شده به موبایل کاربر.
        پس از 3 بار وارد کردن کد اشتباه، شماره موبایل برای 1 ساعت مسدود می‌شود.
        """,
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(
                response=VerifyOTPSerializer,
                description='احراز هویت موفق با توکن‌های JWT'
            ),
            400: OpenApiResponse(
                response=VerifyOTPSerializer,
                description='کد OTP نامعتبر یا منقضی شده'
            ),
            429: OpenApiResponse(
                response=VerifyOTPSerializer,
                description='تعداد درخواست‌ها بیش از حد مجاز'
            )
        },
        examples=[
            OpenApiExample(
                'تأیید موفق',
                value={'phone': '09123456789', 'code': '123456'},
                status_codes=['200']
            ),
            OpenApiExample(
                'کد نامعتبر',
                value={'phone': '09123456789', 'code': '000000'},
                status_codes=['400']
            ),
        ]
    )    
    # چون کاربر برای درخواست به این ویو  احراز هویت نیمخواهد ولی دیتا حساس دارد و در یوزر تغییر ایجاد میکند csrf-protect باید باشد.
    # برای دیتا حساس مثل تایید  این کد  و دیتا های مالی باید از این csrf_protect استفاده کرد
    # در صورت استفاده از jwt authentication به این csrf_protect نیازی ندارید
    @method_decorator(csrf_protect)
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        client_ip, _ = get_client_ip(request)
        # ip = request.META.get('REMOTE_ADDR')


        # if AuthService.is_ip_blocked(ip, 'OTP') or AuthService.is_user_blocked(phone, 'OTP'):
        #     return Response(
        #         {'error': 'Too many failed attempts. Try again later.'},
        #         status=status.HTTP_429_TOO_MANY_REQUESTS
        #     )
        

        
        if not OTPService.check_throttle(client_ip, phone, 'OTP'):
            return Response(
                {'error': f'Too many attempts. Try again after {settings.ATTEMPTS_TIME_RANGE} hour.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        user = get_object_or_404(User,phone=phone)
        if OTPService.verify_otp(phone, code):

            # Authenticate User 
            if not user.is_verified:
                user.is_verified = True
                user.save()

            # Obtain Token
            refresh = RefreshToken.for_user(user)
        
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'phone': user.phone,
                'is_verified': user.is_verified
            })
        else:
            OTPService.record_failed_attempt(client_ip, phone, 'OTP')
            return Response(
                {'error': 'Invalid OTP code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserCustomViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    
    # http_method_names = ['get', 'post', 'delete', 'head', 'options']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes =[IsAdminUser]

        # if create customer beside user    ################
        # elif self.action == 'create':
        #     return UserCreateSerializer
        # else:
        #     return UserSerializer
        

    @action(detail=False , methods=['get','patch','delete'],permission_classes=[IsAuthenticated])
    def me(self,request):
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data,status=status.HTTP_200_OK)

        elif request.method == 'PATCH':
            serializer = UserSerializer(user,data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,status=status.HTTP_205_RESET_CONTENT)

        elif request.method == 'DELETE':
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=False , methods=['put'],permission_classes=[IsAuthenticated]) # change url_path by set  url_path='me/change-pass'
    def change_password(self,request):
        serializer = ChangePasswordSerializer(data=request.data,context={'user':request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully'},status=status.HTTP_205_RESET_CONTENT)




# class ResendOTPAPIView(APIView):
#     throttle_classes = [AnonRateThrottle]
#     @extend_schema(
#         tags=['Authentication'],
#         summary="درخواست مجدد کد OTP",
#         description="""
#         ارسال مجدد کد یکبار مصرف برای شماره موبایل کاربر.
#         محدودیت‌ها:
#         - حداکثر 3 درخواست از یک IP در 1 ساعت
#         - حداکثر 3 درخواست برای یک شماره موبایل در 1 ساعت
#         در صورت نقض محدودیت‌ها، کاربر برای 1 ساعت مسدود می‌شود.
#         """,
#         request=ResendOTPSerializer,
#         responses={
#             200: OpenApiResponse(
#                 response=ResendOTPSerializer,
#                 description='کد OTP جدید با موفقیت ارسال شد'
#             ),
#             400: OpenApiResponse(
#                 response=ResendOTPSerializer,
#                 description='شماره موبایل نامعتبر یا کاربر وجود ندارد'
#             ),
#             429: OpenApiResponse(
#                 response=ResendOTPSerializer,
#                 description='تعداد درخواست‌ها بیش از حد مجاز'
#             )
#         },
#         examples=[
#             OpenApiExample(
#                 'درخواست موفق',
#                 value={'phone': '09123456789'},
#                 status_codes=['200'],
#                 description='کد جدید برای این شماره ارسال خواهد شد'
#             ),
#             OpenApiExample(
#                 'شماره نامعتبر',
#                 value={'phone': '0912'},
#                 status_codes=['400'],
#                 description='فرمت شماره موبایل نادرست است'
#             ),
#             OpenApiExample(
#                 'محدودیت درخواست',
#                 value={'phone': '09123456789'},
#                 status_codes=['429'],
#                 description='تعداد درخواست‌ها از حد مجاز بیشتر شده است'
#             ),
#         ],

#     )
#     def post(self, request):
#         serializer = ResendOTPSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         phone = serializer.validated_data['phone']
#         # ip = request.META.get('REMOTE_ADDR')
#         client_ip, _ = get_client_ip(request)
        
#         if not OTPService.check_throttle(client_ip, phone, attempt_type='OTP'):
#             return Response(
#                 {'error': 'Too many attempts. Try again after 1 hour.'},
#                 status=status.HTTP_429_TOO_MANY_REQUESTS
#             )
#         # if AuthService.is_ip_blocked(ip, 'OTP') or AuthService.is_user_blocked(phone, 'OTP'):
#         #     return Response(
#         #         {'error': 'Too many attempts. Try again later.'},
#         #         status=status.HTTP_429_TOO_MANY_REQUESTS
#         #     )

#         code = OTPService.generate_otp(phone)

#         # Send OTP-Code to User's phone

#         return Response({
#             'success': True,
#             'message': 'New OTP sent successfully',
#             'phone': phone
#         })
    



# class CompleteProfileAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     @extend_schema(
#         tags=['User'],
#         summary="تکمیل اطلاعات کاربر",
#         description="تکمیل اطلاعات پروفایل کاربر پس از ثبت‌نام اولیه",
#         request=CompleteProfileSerializer,
#         responses={
#             200: OpenApiResponse(
#                 response=CompleteProfileSerializer,
#                 description='اطلاعات کاربر با موفقیت به‌روزرسانی شد'
#             ),
#             400: OpenApiResponse(
#                 response=CompleteProfileSerializer,
#                 description='داده‌های ورودی نامعتبر'
#             )
#         },
#         examples=[
#             OpenApiExample(
#                 'درخواست موفق',
#                 value={
#                     'first_name': 'علی',
#                     'last_name': 'محمدی',
#                     'email': 'ali@example.com',
#                     'password': 'NewSecurePassword123'
#                 },
#                 status_codes=['200']
#             ),
#         ]
#     )
#     def post(self, request):
#         serializer = CompleteProfileSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         user = request.user
#         user.first_name = serializer.validated_data['first_name']
#         user.last_name = serializer.validated_data['last_name']
#         user.email = serializer.validated_data['email']
        
#         if 'password' in serializer.validated_data:
#             user.set_password(serializer.validated_data['password'])
        
#         user.save()
        
#         return Response({
#             'success': True,
#             'message': 'Profile completed successfully'
#         })