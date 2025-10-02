from rest_framework.throttling import UserRateThrottle


class ApiBurstRateThrottle(UserRateThrottle):
    scope = 'burst'


class OtpBurstRateThrottle(UserRateThrottle):
    scope = 'otp-burst'


class OtpSustainedRateThrottle(UserRateThrottle):
    scope = 'otp-sustained'
