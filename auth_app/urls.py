from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import RegisterAPIView, LoginAPIView, OTPVerificationView, UserCustomViewSet




router = SimpleRouter()
router.register(r'users', UserCustomViewSet)

urlpatterns = [
    path('',include(router.urls)),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('jwt/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),

]

