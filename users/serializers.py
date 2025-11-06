from django.contrib.auth import get_user_model, password_validation, authenticate
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator

from users.models import Address, Point

User = get_user_model()

class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="이미 등록된 이메일입니다.")
        ]
    )

    class Meta:
        model = User
        fields = ["email", "password", "username", "nickname", "phone_number"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        pwd = validated_data.pop('password')
        try:
            user = User.objects.create_user(password=pwd, **validated_data, status="ready")
            return user
        except IntegrityError:
            raise serializers.ValidationError({"email": "이미 등록된 이메일입니다."})

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        password = attrs["password"]

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError("이메일 또는 비밀번호를 확인해주세요.")
        if not user.is_active:
            raise serializers.ValidationError("이메일 인증을 완료해주세요.")
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

class MeUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["password"]

    def validate_password(self, value):
        password_validation.validate_password(value, user=self.instance)
        return value

    def update(self, instance, validated_data):
        new_password = validated_data.get("password")
        instance.set_password(new_password)
        instance.save(update_fields=["password"])
        return instance

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "nickname", "phone_number"]
        read_only_fields = ["email", "username", "nickname", "phone_number"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "address_name", "recipient", "recipient_phone", "post_code", "address", "detail_address"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, attrs):
        return attrs


class PointListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Point
        fields = ["id", "amount", "balance", "created_at", "updated_at"]
        read_only_fields = fields

class PointBalanceSerializer(serializers.Serializer):
    balance = serializers.IntegerField(read_only=True)