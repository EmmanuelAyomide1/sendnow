from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Otp


class SignUpSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()

    class Meta:
        model = get_user_model()
        fields = ["phone_number",]

    def validate_phone_number(self, value):
        return value

    def create(self, validated_data):
        return (
            get_user_model().objects.filter(
                phone_number=validated_data['phone_number'],
                phone_verified=True
            ).first()
            or get_user_model().objects.create_user(**validated_data)
        )


class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, phone_number):
        self.user = get_user_model().objects.filter(
            phone_number=phone_number).first()
        if not self.user:
            raise serializers.ValidationError(
                'Phone Number does not exist')
        return phone_number


class OTPVerificationSerializer(serializers.Serializer):
    code = serializers.CharField()
    phone_number = serializers.CharField()

    def validate(self, attrs):
        code = attrs.get('code')
        phone_number = attrs.get('phone_number')

        try:
            user = get_user_model().objects.get(phone_number=phone_number)
            otp = Otp.objects.get(otp=code, user=user)
            if otp.is_valid():
                # invalidate otp
                otp.use()

                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Invalid OTP')

        except Exception as e:
            raise serializers.ValidationError('Invalid OTP or Phone Number')


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
