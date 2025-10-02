from email.policy import default
from django.contrib.auth import get_user_model

from rest_framework import serializers

from users.utils import format_phone_number, verify_phone_number_format

from .models import Otp, SavedContact


class SignUpSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = [
            "phone_number",
        ]

    def validate_phone_number(self, value):
        if not verify_phone_number_format(value):
            raise serializers.ValidationError(
                f'Enter a valid phone number, example "+2341234567345"'
            )

        # Format number
        phone_number = format_phone_number(value)
        return phone_number

    def create(self, validated_data):
        print(validated_data["phone_number"])
        return get_user_model().objects.filter(
            phone_number=validated_data["phone_number"],
        ).first() or get_user_model().objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = get_user_model()
        fields = ["id", "name", "description", "profile_picture"]
        # extra_kwargs = {
        #     "phone_number": {'read_only': True}
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check context to determine if this is for registration
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            user = request.user

            if user.name:
                self.fields["name"].required = False


class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, phone_number):
        self.user = get_user_model().objects.filter(phone_number=phone_number).first()
        if not self.user:
            raise serializers.ValidationError("Phone Number does not exist")
        return phone_number


class OTPVerificationSerializer(serializers.Serializer):
    code = serializers.CharField()
    phone_number = serializers.CharField()

    def validate(self, attrs):
        code = attrs.get("code")
        phone_number = attrs.get("phone_number")
        phone_number = format_phone_number(phone_number)

        try:
            user = get_user_model().objects.get(phone_number=phone_number)
            otp = Otp.objects.get(otp=code, user=user)
            if otp.is_valid():
                # invalidate otp
                otp.use()

                attrs["user"] = user
                return attrs
            else:
                raise serializers.ValidationError("Invalid OTP")

        except Exception as e:
            print(str(e))
            raise serializers.ValidationError("Invalid OTP or Phone Number")


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class SavedContactSerializer(serializers.ModelSerializer):
    contact = serializers.SerializerMethodField("get_contact")
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), write_only=True, source="contact"
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SavedContact
        fields = ["id", "contact", "contact_id", "user"]

    def validate_contact_id(self, contact):
        user = self.context["request"].user

        if SavedContact.objects.filter(contact=contact, user=user).exists():
            raise serializers.ValidationError(
                {"contact": "This contact is already saved."}
            )

        return contact

    def get_contact(self, obj):
        return {
            "id": obj.contact.id,
            "name": obj.contact.name,
            "phone_number": obj.contact.phone_number,
        }
