from rest_framework.throttling import AnonRateThrottle



class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'

class OTPRateThrottle(AnonRateThrottle):
    scope = 'otp'

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

