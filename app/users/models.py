import datetime
import random
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel

from .utils import verify_phone_number_format


# Create your models here.
class CustomUserManager(BaseUserManager):
    def _validate_phone_number(self, phone_number):
        """
        Phone number validation
        """
        if not phone_number:
            raise DjangoValidationError('Phone number is required')

        if not verify_phone_number_format(phone_number):
            raise DjangoValidationError('Enter a valid phone number')

        return phone_number

    def create_user(self, phone_number, name=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone_number field must be set")

        phone_number = self._validate_phone_number(phone_number)

        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('phone_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=225, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='user/profile', null=True, blank=True)
    phone_number = models.CharField(
        max_length=15, unique=True, null=False, blank=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CustomUserManager()

    username = None
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number


class Otp(TimeStampedModel):
    otp = models.CharField(max_length=6)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.otp} - {self.user.phone_number}"

    @classmethod
    def generate_otp(cls, user, expiry_minutes=2):
        """
        Generate a new OTP for the given user
        """
        # Invalidate existing unused OTPs for this user and purpose
        cls.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(is_used=True)

        # Generate a new OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + datetime.timedelta(minutes=expiry_minutes)

        # Create and save new OTP
        otp_obj = cls.objects.create(
            otp=otp_code,
            user=user,
            expires_at=expires_at
        )

        return otp_obj

    def is_valid(self):
        """
        Check if the OTP is valid (not expired and not used)
        """
        return not self.is_used and self.expires_at > timezone.now()

    def use(self):
        """
        Mark the OTP as used
        """
        self.is_used = True
        self.save(update_fields=['is_used', 'updated_at'])

    @classmethod
    def verify_otp(cls, user, otp_code):
        """
        Verify an OTP for a user and mark it as used if valid
        """
        try:
            otp_obj = cls.objects.get(
                user=user,
                otp=otp_code,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            otp_obj.use()
            return True
        except cls.DoesNotExist:
            return False


class SavedContact(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="saved_contacts")
    contact = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="in_saved_contacts")
