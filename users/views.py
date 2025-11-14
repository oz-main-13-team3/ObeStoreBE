import logging
from urllib.parse import quote

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.core.signing import BadSignature, SignatureExpired
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.views import View
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .auth import blacklist_jti, is_blacklisted
from .models import Address, Point, SocialLogin
from .serializers import (
    AddressSerializer,
    LoginSerializer,
    MeSerializer,
    MeUpdateSerializer,
    PointListSerializer,
    SignUpSerializer,
)

User = get_user_model()

EMAIL_VERIFY_SALT = "verify-email"

logger = logging.getLogger(__name__)


def make_email_token(email: str) -> str:
    return signing.dumps({"email": email}, salt=EMAIL_VERIFY_SALT)


def parse_email_token(token: str) -> str:
    max_age = getattr(settings, "EMAIL_VERIFY_MAX_AGE", 60 * 60 * 24)
    data = signing.loads(token, salt=EMAIL_VERIFY_SALT, max_age=max_age)
    return data["email"]


# 회원가입, 내정보, 이메일인증, 포인트, 배송지
class UsersViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.Serializer

    @extend_schema(
        methods=["post"],
        description="회원가입을 하고 이메일 인증 링크를 전송",
        request=SignUpSerializer,
        responses={201: {"description": "회원가입 완료"}},
    )
    @action(detail=False, methods=["post"], url_path="signup", permission_classes=[permissions.AllowAny])
    def signup(self, request):
        ser = SignUpSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()

        # 인증용 토큰 생성
        code = make_email_token(user.email)
        frontend_base = getattr(settings, "FRONTEND_BASE_URL", None)
        if frontend_base:
            verify_url = f"{frontend_base.rstrip('/')}/users/email/verify?code={code}"
        else:
            verify_url = request.build_absolute_uri(f"/users/email/verify?code={code}")

        if settings.DEBUG:
            logger.debug(f"[EMAIL VERIFY URL] {verify_url}")
        else:
            subject = "[ObeStore] 이메일 인증을 완료해주세요."
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [user.email]
            html = render_to_string(
                "emails/verify_email.html",
                {
                    "username": user.username,
                    "verify_url": verify_url,
                    "preheader": "버튼을 눌러 ObeStore 이메일 인증을 완료하세요.",
                },
            )
            text = f"다음 링크를 클릭해 인증을 완료하세요:\n{verify_url}"

            msg = EmailMultiAlternatives(subject, text, from_email, to)
            msg.attach_alternative(html, "text/html")
            msg.send(fail_silently=False)

        return Response({"detail": "회원가입 완료! 이메일 인증을 진행해주세요.","login_type": getattr(user, "_login_type", "email"),}, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=["get"],
        description="내 정보 조회(GET)",
        responses={200: MeSerializer},
    )
    @extend_schema(
        methods=["patch"],
        description="비밀번호 변경(PATCH)",
        request=MeUpdateSerializer,
        responses={200: {"description": "비밀번호 변경 완료"}},
    )
    @extend_schema(
        methods=["delete"],
        description="회원탈퇴(DELETE)",
        responses={204: {"description": "삭제 완료"}},
    )
    @action(
        detail=False,
        methods=["get", "patch", "delete"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        if request.method == "GET":
            return Response(MeSerializer(request.user).data)

        if request.method == "PATCH":
            if "password" not in request.data or not request.data.get("password"):
                return Response({"detail": "password 필드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
            ser = MeUpdateSerializer(request.user, data=request.data, partial=False)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response({"detail": "비밀번호가 변경되었습니다."})

        request.user.status = "dormancy"
        request.user.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["get"],
        description="이메일 인증 링크 검증",
        parameters=[
            OpenApiParameter(
                name="code",
                type=str,
                location="query",
                description="이메일 인증 토큰 코드 (?code=...)",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description="이메일 인증 성공"),
            400: OpenApiResponse(description="잘못되거나 만료된 코드"),
        },
    )
    @action(detail=False, methods=["get"], url_path="email/verify", permission_classes=[permissions.AllowAny])
    def email_verify(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "code 파라미터가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = parse_email_token(code)
            user = User.objects.get(email=email)
            if user.status != "active":
                user.status = "active"
                user.save(update_fields=["status"])
            frontend_base = getattr(settings, "FRONTEND_BASE_URL", None)
            if frontend_base:
                return redirect(f"{frontend_base.rstrip('/')}/email-verified")
            return Response({"detail": "이메일 인증이 완료되었습니다."}, status=200)
        except SignatureExpired:
            return Response(
                {"detail": "인증 링크가 만료되었습니다. 재발송을 요청하세요."}, status=status.HTTP_400_BAD_REQUEST
            )
        except (BadSignature, User.DoesNotExist, KeyError, ValueError):
            return Response({"detail": "유효하지 않은 링크입니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 포인트 내역 조회..
    @extend_schema(
        methods=["get"],
        description="로그인된 사용자의 포인트 내역 조회",
        responses={200: OpenApiResponse(response=PointListSerializer(many=True))},
    )
    @action(detail=False, methods=["get"], url_path="me/points", permission_classes=[permissions.IsAuthenticated])
    def points(self, request):
        qs = Point.objects.filter(user=request.user).order_by("-created_at", "-id")
        return Response(PointListSerializer(qs, many=True).data, status=200)

    # 포인트 잔액 조회
    @extend_schema(
        methods=["get"],
        description="로그인된 사용자의 포인트 잔액 조회",
        responses={
            200: OpenApiResponse(
                description="현재 포인트 잔액",
                examples=[OpenApiExample("잔액 예시", value={"balance": 12000}, response_only=True)],
            )
        },
    )
    @action(
        detail=False, methods=["get"], url_path="me/points/balance", permission_classes=[permissions.IsAuthenticated]
    )
    def points_balance(self, request):
        last = Point.objects.filter(user=request.user).order_by("-created_at", "-id").first()
        current = last.amount if last else 0
        return Response({"balance": current}, status=200)

    @extend_schema(
        methods=["get"],
        description="사용자의 배송지 조회(GET)",
        responses={200: OpenApiResponse(response=AddressSerializer(many=True))},
    )
    @extend_schema(
        methods=["post"],
        description="배송지 등록(POST)",
        request=AddressSerializer,
        responses={
            201: OpenApiResponse(
                description="배송지 등록 성공",
                response=AddressSerializer,
            )
        },
    )
    @extend_schema(
        methods=["patch"],
        description="배송지 수정(PATCH)",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="query",
                description="수정할 배송지 ID (PATCH 시 필수)",
                required=True,
            ),
        ],
        request=AddressSerializer,
        responses={200: OpenApiResponse(response=AddressSerializer)},
    )
    @action(
        detail=False,
        methods=["get", "post", "patch", "delete"],
        url_path="me/address",
        permission_classes=[permissions.IsAuthenticated],
    )
    def address(self, request):
        user = request.user

        if request.method == "GET":
            qs = Address.objects.filter(user=user).order_by("-updated_at")
            return Response(AddressSerializer(qs, many=True).data, status=200)

        if request.method == "POST":
            ser = AddressSerializer(data=request.data, context={"request": request})
            ser.is_valid(raise_exception=True)
            obj = ser.save()
            return Response(AddressSerializer(obj).data, status=201)

        addr_id = request.query_params.get("id")
        if not addr_id:
            return Response({"detail": "쿼리 파라미터 Id가 필요합니다."}, status=400)

        addr = get_object_or_404(Address, pk=addr_id, user=user)

        if request.method == "PATCH":
            ser = AddressSerializer(addr, data=request.data, partial=True, context={"request": request})
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data, status=200)

        addr.delete()
        return Response(status=204)


# login, logout, tokenrefresh
class SessionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        methods=["post"],
        description="로그인 (access / refresh 토큰 발급)",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="로그인 성공",
                examples=[
                    OpenApiExample(
                        "로그인 예시", value={"access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}, response_only=True
                    )
                ],
            ),
            400: OpenApiResponse(description="유효하지 않은 로그인 정보"),
        },
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        ser = LoginSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        tokens = ser.save()

        resp = Response({"access": tokens["access"]}, status=200)
        secure = not settings.DEBUG
        refresh_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
        access_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())

        resp.set_cookie(
            "refresh_token",
            tokens["refresh"],
            max_age=refresh_age,
            secure=secure,
            httponly=True,
            samesite="None",
            path="/",
        )
        resp.set_cookie(
            "access_token",
            tokens["access"],
            max_age=access_age,
            secure=secure,
            httponly=True,
            samesite="None",
            path="/",
        )
        return resp

    @extend_schema(
        summary="로그아웃",
        description="AccessToken을 이용해 로그아웃을 할 수 있습니다.",
        request=inline_serializer(
            name="LogoutRequest",
            fields={"refresh": serializers.CharField(required=False, help_text="Optional refresh token")},
        ),
        responses={204: None},
        tags=["session"],
    )
    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        # access 블랙리스트
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if auth.startswith("Bearer "):
            raw_access = auth.split(" ", 1)[1]
            try:
                at = AccessToken(raw_access)
                blacklist_jti(at["jti"], int(at["exp"]))
            except TokenError:
                pass

        # refresh 블랙리스트
        refresh = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        if refresh:
            try:
                rt = RefreshToken(refresh)
                blacklist_jti(rt["jti"], int(rt["exp"]))
            except TokenError:
                pass

        resp = Response(status=204)
        resp.delete_cookie("refresh_token", path="/")
        resp.delete_cookie("access_token", path="/")
        return resp

    @extend_schema(
        summary="토큰 갱신",
        description="Refresh 토큰을 이용해 새로운 access 토큰을 발급합니다. body나 쿠키에서 refresh 토큰을 받을 수 있습니다.",
        request=inline_serializer(
            name="TokenRefreshRequest", fields={"refresh": serializers.CharField(required=False, allow_blank=True)}
        ),
        responses={
            200: inline_serializer(name="TokenRefreshResponse", fields={"access": serializers.CharField()}),
            400: inline_serializer(name="TokenRefreshError", fields={"detail": serializers.CharField()}),
        },
        tags=["session"],
    )
    @action(detail=False, methods=["post"], url_path="token/refresh")
    def token_refresh(self, request):
        refresh = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        if not refresh:
            return Response({"detail": "refresh 토큰이 필요합니다."}, status=400)
        try:
            rt = RefreshToken(refresh)
            if is_blacklisted(rt["jti"]):
                return Response({"detail": "블랙리스트 처리된 refresh 토큰입니다."}, status=400)
            return Response({"access": str(rt.access_token)}, status=200)
        except TokenError:
            return Response({"detail": "유효하지 않은 refresh 토큰입니다."}, status=400)


class NaverLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="네이버 로그인",
        description="사용자를 네이버 로그인 페이지로 리다이렉트합니다.",
        request=None,
        responses={302: None},  # 리다이렉트 상태 코드
        tags=["oauth"],
    )
    def get(self, request):
        client_id = settings.NAVER_CLIENT_ID
        redirect_uri = quote(settings.NAVER_REDIRECT_URI, safe="")
        state = get_random_string(32)

        request.session["naver_oauth_state"] = state

        naver_auth_url = (
            "https://nid.naver.com/oauth2.0/authorize"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )

        return redirect(naver_auth_url)


class NaverCallbackView(View):
    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        secure = not settings.DEBUG

        if not code:
            return JsonResponse({"error": "Missing authorization code."}, status=400)

        token_url = "https://nid.naver.com/oauth2.0/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.NAVER_CLIENT_ID,
            "client_secret": settings.NAVER_CLIENT_SECRET,
            "code": code,
            "state": state,
        }

        token_response = requests.get(token_url, params=data)
        token_data = token_response.json()

        access_token = token_data.get("access_token")
        if not access_token:
            return JsonResponse({"error": "Failed to get access token.", "detail": token_data}, status=400)

        profile_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(profile_url, headers=headers)
        profile_data = profile_response.json()

        user_info = profile_data.get("response", {})
        email = user_info.get("email")
        name = user_info.get("name")
        nickname = user_info.get("nickname")
        phone_number = user_info.get("mobile", "").replace("-", "")

        if not email:
            return JsonResponse({"error": "Email not provided by Naver."}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": name,
                "nickname": nickname,
                "phone_number": phone_number,
                "status": "active",
            },
        )
        if created:
            user.set_unusable_password()
            user.save()

        provider_user_id = int(user_info.get("id"))
        SocialLogin.objects.update_or_create(
            user=user,
            provider="naver",
            provider_user_id=provider_user_id,
            defaults={
                "access_token": access_token,
                "refresh_token": token_data.get("refresh_token", "")
            }
        )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        response = JsonResponse(
            {
                "message": "Naver login success",
                "email": email,
                "username": name,
                "nickname": nickname,
                "login_type": "naver",
            }
        )
        response.set_cookie("access_token", str(access), httponly=True, samesite="None", secure=secure)
        response.set_cookie("refresh_token", str(refresh), httponly=True, samesite="None", secure=secure)
        return response
