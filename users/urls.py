from django.urls import path
from .views import (
    SignUpView,
    LogoutView,
    RefreshTokenView,
    OTPVerificationView,
    ResendOTPView,
)


urlpatterns = [
    path("signup", SignUpView.as_view(), name="signup"),
    path("refresh-token", RefreshTokenView.as_view(), name="refresh-token"),
    path("verify-otp", OTPVerificationView.as_view(), name="verify-otp"),
    path("resend-otp", ResendOTPView.as_view(), name="resend-otp"),
    path("logout", LogoutView.as_view(), name="logout"),
]
