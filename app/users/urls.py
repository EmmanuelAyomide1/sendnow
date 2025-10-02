from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    SavedContactsViewset,
    LogoutView,
    RefreshTokenView,
    OTPVerificationView,
    ResendOTPView,
    UserViewset,
    VerifyPhoneNumberView,
)


app_name = "user"

router = DefaultRouter()
router.register(r"saved/contacts", SavedContactsViewset)
router.register("", UserViewset)

urlpatterns = [
    path("auth/verify-phone", VerifyPhoneNumberView.as_view(), name="user"),
    path("auth/refresh-token", RefreshTokenView.as_view(), name="refresh-token"),
    path("auth/verify-otp", OTPVerificationView.as_view(), name="verify-otp"),
    path("auth/resend-otp", ResendOTPView.as_view(), name="resend-otp"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
] + router.urls
