from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.core.validators import MinLengthValidator
from utils.models import TimestampModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일을 입력해주세요.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("슈퍼유저는 is_staff=True 이어야 합니다.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("슈퍼유저는 is_superuser=True 이어야 합니다.")

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, TimestampModel):
    email = models.EmailField(max_length=100, null=False,unique=True, verbose_name="이메일")
    password = models.CharField(max_length=255, null=False,verbose_name="비밀번호")
    username = models.CharField(max_length=30, null=False,verbose_name="이름")
    nickname = models.CharField(max_length=30, validators=[MinLengthValidator(6)], null=False,verbose_name="닉네임")
    phone_number = models.CharField(max_length=15, null=False,verbose_name="휴대폰번호")
    is_staff = models.BooleanField(default=False, verbose_name="관리자권한")
    is_active = models.BooleanField(default=False, verbose_name="계정상태")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"

    def __str__(self):
        return f"{self.nickname} ({self.email})"

class SocialLogin(TimestampModel):
    PROVIDER_CHOICES = ("naver", "naver")

    user_id = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="social_logins"
    )

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True, verbose_name="제공자")
    provider_user_id = models.BigIntegerField(verbose_name="제공자 측 고유 ID")
    access_token = models.TextField(verbose_name="엑세스 토큰")
    refresh_token = models.TextField(verbose_name="리프레쉬 토큰")

    class Meta:
        db_table = "social_login"
        verbose_name = "소셜 로그인"
        verbose_name_plural = "소셜 로그인 목록"

    def __str__(self):
        return f"{self.provider} - {self.provider_user_id}"


class Address(TimestampModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, #지워지게하기로했던가..?
        related_name='addresses',
        verbose_name='사용자'
    )
    address_name = models.CharField(max_length=30, null=False, verbose_name="배송지명")
    recipient = models.CharField(max_length=30, null=False, verbose_name="수취인")
    recipient_phone = models.CharField(max_length=15, verbose_name="수취인번호")
    post_code = models.CharField(max_length=10, verbose_name="우편번호")
    address = models.CharField(max_length=200, null=False, verbose_name="주소")
    detail_address = models.CharField(max_length=200, null=False, verbose_name="상세주소")

    class Meta:
        verbose_name = "배송지"
        verbose_name_plural = "배송지 목록"
        ordering = ('-updated_at',) # 최신 내역이 위로 오도록
        db_table = "" #추후수정~

    def str(self):
        return self.address_name


class Point(TimestampModel):
    user = models.ForeignKey(
        User,
        related_name='points',
        verbose_name='회원번호'
    )

    amount = models.IntegerField(default=0, verbose_name="현재 포인트 잔액")
    balance = models.IntegerField(verbose_name="포인트 변화량")

    class Meta:
        verbose_name = "포인트 내역"
        verbose_name_plural = "포인트 내역 목록"
        ordering = ('-updated_at',) # 최신 내역이 위로 오도록
        db_table = "" #추후수정~

    def str(self):
        return f'잔액: {self.amount}'