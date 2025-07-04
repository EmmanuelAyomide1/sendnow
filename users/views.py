from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import views, status

from core.utils import custom_exception_handler
from users.utils import send_OTP_using_vonage

from .models import Otp
from .serializers import (
    LogoutSerializer,
    OTPVerificationSerializer,
    ResendOTPSerializer,
    SignUpSerializer
)


# Create your views here.
class SignUpView(views.APIView):
    permission_classes = []
    serializer_class = SignUpSerializer

    @transaction.atomic
    @swagger_auto_schema(
        tags=["Authentication"],
        request_body=SignUpSerializer,
        operation_summary="Register a user and or Send OTP to a user",
        operation_description="Registers a user on the platform and/or sends an OTP to the user's phone number for verification.",
        responses={
            201: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "message": "OTP sent successfully, check your messages for verification"
                    }
                }
            ),
            400: openapi.Response(
                description="Validation Errors",
                examples={
                    "application/json":
                        {
                            "phone_number": ["Enter a valid Phone number."],
                        }
                }
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # send otp
        user = serializer.instance
        otp_obj = Otp.generate_otp(user=user)

        sent = send_OTP_using_vonage(
            phone_number=serializer.validated_data['phone_number'],
            otp=otp_obj.otp
        )
        print("OTP sent to user", {
            "phone_number": user.phone_number,
            "otp": otp_obj.otp
        })

        if not sent:
            return Response({'message': 'Enter a valid Phone number'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "OTP sent successfully, check your message for verification"},
            status=status.HTTP_201_CREATED,
        )


class ResendOTPView(views.APIView):
    """
    Resends the OTP to the user
    """
    serializer_class = ResendOTPSerializer
    permission_classes = []

    @swagger_auto_schema(
        tags=['Authentication'],
        request_body=serializer_class,
        operation_summary='Resend OTP',
        operation_description='Resends the OTP to the user via email.',
        responses={
            200: openapi.Response(
                description="OTP resent successfully",
                examples={
                    "application/json": {
                        "message": "OTP resent successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Validation Errors",
                examples={
                    "application/json": {
                        "phone_number": "Phone Number does not exist.",
                        "phine_number": "Enter a valid Phone number."
                    }
                }
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        otp_obj = Otp.generate_otp(user=user)
        sent = send_OTP_using_vonage(
            phone_number=serializer.validated_data['phone_number'],
            otp=otp_obj.otp
        )
        print("OTP resent to user", {
            "phone_number": user.phone_number,
            "otp": otp_obj.otp
        })

        if not sent:
            return Response({'message': 'Enter a valid Phone number'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP resent successfully'}, status=status.HTTP_200_OK)


class OTPVerificationView(views.APIView):
    """
    Verifies a user by validating an OTP
    """
    serializer_class = OTPVerificationSerializer
    permission_classes = []

    @swagger_auto_schema(
        tags=["Authentication"],
        request_body=serializer_class,
        operation_summary="Verify OTP",
        operation_description="Verifies a user by validating an OTP",
        responses={
            200: "OTP Verified successfully",
            400: "Otp matching query does not exist",
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user = validated_data['user']

        # set email as verified
        user.phone_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message': 'OTP Verified successfully',
            "tokens": {
                "access_token": access_token,
                "refresh_token": str(refresh)
            }
        })


class RefreshTokenView(views.APIView):
    permission_classes = []
    serializer_class = LogoutSerializer

    @swagger_auto_schema(
        tags=["Authentication"],
        request_body=serializer_class,
        operation_summary="Refresh token",
        operation_description="Refreshes the access token using the refresh token",
        responses={
            200: "Token refreshed successfully",
            400: "Bad Request",
            500: "An error occurred while refreshing token",
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'message': 'Refresh token not included'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({'access_token': access_token})
        except InvalidToken as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f'An error occurred while refreshing token: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(views.APIView):
    permission_classes = []
    serializer_class = LogoutSerializer

    @swagger_auto_schema(
        tags=["Authentication"],
        request_body=serializer_class,
        operation_summary="Logout",
        operation_description="Logs out a user by blacklisting their refresh token",
        responses={
            200: "Successfully logged out",
            400: "Bad Request",
            500: "Could not log out",
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({'message': 'Refresh token not included'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()

            return Response({'message': 'Succesfully Logged out'}, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({'message': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': 'Could not log out'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
