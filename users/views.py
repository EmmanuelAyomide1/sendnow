from django.contrib.auth import authenticate
from django.db import transaction

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import views, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from core.throttles import OtpBurstRateThrottle, ApiBurstRateThrottle, OtpSustainedRateThrottle

from .utils import send_sms_using_africa_talk
from .models import Otp
from .schemas import list_of_strings_schema, object_of_string_schema
from .serializers import (
    LogoutSerializer,
    OTPVerificationSerializer,
    ResendOTPSerializer,
    SignUpSerializer,
    UserSerializer
)


# Create your views here.
class SignUpView(views.APIView):
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ApiBurstRateThrottle, OtpSustainedRateThrottle]

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAuthenticated()]
        return [AllowAny()]

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
                },
                schema=object_of_string_schema("message")
            ),
            400: openapi.Response(
                description="Validation Errors",
                examples={
                    "application/json":
                        {
                            "phone_number": ["Enter a valid Phone number."],
                        }
                },
                schema=list_of_strings_schema("phone_number")
            ),
        },
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # send otp
        user = serializer.instance
        otp_obj = Otp.generate_otp(user=user)

        sent = send_sms_using_africa_talk(
            phone_number=serializer.validated_data['phone_number'],
            otp=otp_obj.otp
        )
        print("OTP sent to user", {
            "phone_number": user.phone_number,
            "otp": otp_obj.otp
        })

        if not sent:
            return Response({'message': 'Enter a valid Phone number'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "OTP sent successfully, check your message for verification",
            "new_user": not user.phone_verified
        },
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        tags=["Authentication"],
        request_body=UserSerializer,
        operation_summary="Updates user attributes",
        operation_description="Update user attributes",
        responses={
            200: UserSerializer,
            400: openapi.Response(
                description="Validation Errors",
                examples={
                    "application/json":
                        {
                            "name": ["Name should be at most 20 characters long"],
                        },
                },
                schema=list_of_strings_schema("name")
            ),
            401: openapi.Response(description="Authentication required"),
            404: openapi.Response(description="User not found"),
        },
    )
    def patch(self, request):
        print("Files:", request.FILES)
        print("profile_picture in data:", 'profile_picture' in request.data)
        print("profile_picture value:", request.data.get('profile_picture'))
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'data': serializer.data, 'message': 'updated user successfully'})


class ResendOTPView(views.APIView):
    """
    Resends the OTP to the user
    """
    serializer_class = ResendOTPSerializer
    permission_classes = []
    throttle_classes = [OtpBurstRateThrottle, OtpSustainedRateThrottle]

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
                },
                schema=object_of_string_schema("message")
            ),
            400: openapi.Response(
                description="Validation Errors",
                examples={
                    "application/json": {
                            "phone_number": [
                                "Phone Number does not exist.",
                                "Enter a valid Phone number."
                            ],
                    },
                },
                schema=list_of_strings_schema("phone_number")
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        otp_obj = Otp.generate_otp(user=user)
        sent = send_sms_using_africa_talk(
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
        authenticate(user)
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
