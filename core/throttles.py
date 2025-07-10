from rest_framework.throttling import ScopedRateThrottle


class ApiBurstRateThrottle(ScopedRateThrottle):
    scope = 'burst'


class OtpBurstRateThrottle(ScopedRateThrottle):
    scope = 'otp-burst'


class OtpSustainedRateThrottle(ScopedRateThrottle):
    scope = 'otp-sustained'
