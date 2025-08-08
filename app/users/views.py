from django.contrib.auth import authenticate, get_user_model
from django.db import transaction

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from core.permissions import IsAuthenticationAndRegistered
from core.throttles import OtpBurstRateThrottle, ApiBurstRateThrottle, OtpSustainedRateThrottle

from .utils import format_phone_number, send_sms_using_africa_talk
from .models import Otp, SavedContact
from .schemas import list_of_strings_schema, object_of_string_schema
from .serializers import (
    LogoutSerializer,
    OTPVerificationSerializer,
    ResendOTPSerializer,
    SavedContactSerializer,
    SignUpSerializer,
    UserSerializer
)


# Create your views here.
class VerifyPhoneNumberView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ApiBurstRateThrottle, OtpSustainedRateThrottle]

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
        },
            status=status.HTTP_201_CREATED,
        )


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

        # authenticate user
        authenticate(user)

        # set phone_number as verified
        user.phone_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message': 'OTP Verified successfully',
            'new_user': not bool(user.name),
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
    permission_classes = [IsAuthenticated]
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


class UserViewset(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = get_user_model().objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = UserSerializer
    search_fields = ["name"]
    lookup_field = "phone_number"

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAuthenticated()]
        return [IsAuthenticationAndRegistered()]

    def get_object(self):
        phone_number = self.kwargs.get(self.lookup_field)
        phone_number = format_phone_number(phone_number)
        return get_object_or_404(get_user_model(), phone_number=phone_number)

    @swagger_auto_schema(
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
    @action(detail=False, methods=['patch'], url_path='profile')
    def update_profile(self, request):
        print("Files:", request.FILES)
        print("profile_picture in data:", 'profile_picture' in request.data)
        print("profile_picture value:", request.data.get('profile_picture'))
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'data': serializer.data, 'message': 'updated user successfully'})


class SavedContactsViewset(viewsets.ModelViewSet):
    queryset = SavedContact.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]
    search_fields = ["contact__phone_number", "contact__name"]
    serializer_class = SavedContactSerializer
