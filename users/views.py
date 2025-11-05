from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .auth import blacklist_jti, is_blacklisted
from .serializers import LoginSerializer, MeSerializer, MeUpdateSerializer, SignUpSerializer

User = get_user_model()

EMAIL_VERIFY_SALT = "verify-email"


def make_email_token(email: str) -> str:
    return signing.dumps({"email": email}, salt=EMAIL_VERIFY_SALT)


def parse_email_token(token: str) -> str:
    max_age = getattr(settings, "EMAIL_VERIFY_MAX_AGE", 60 * 60 * 24)
    data = signing.loads(token, salt=EMAIL_VERIFY_SALT, max_age=max_age)
    return data["email"]


# 회원가입, 내정보, 이메일인증
class UsersViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    @action(detail=False, methods=["post"], url_path="signup", permission_classes=[permissions.AllowAny])
    def signup(self, request):
        ser = SignUpSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()

        # 인증용 토큰 생성
        code = make_email_token(user.email)
        host = request.get_host()
        verify_url = f"{request.scheme}://{host}/users/email/verify?code={code}"

        if settings.DEBUG:
            print("[EMAIL VERIFY URL]", verify_url)
        else:
            subject = "[ObeStore] 이메일 인증을 완료해주세요."
            html_message = f"링크를 클릭해 인증을 완료하세요 : {verify_url}"
            send_mail(subject, None, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)

        return Response({"detail": "회원가입 완료! 이메일 인증을 진행해주세요."}, status=status.HTTP_201_CREATED)

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

            return Response({"detail": "이메일 인증이 완료되었습니다."}, status=200)
            # 추후 변경
            # return redirect(f"{getattr(settings, 'FRONTEND_BASE_URL', '/')}/email-verified")
        except SignatureExpired:
            return Response(
                {"detail": "인증 링크가 만료되었습니다. 재발송을 요청하세요."}, status=status.HTTP_400_BAD_REQUEST
            )
        except (BadSignature, User.DoesNotExist, KeyError, ValueError):
            return Response({"detail": "유효하지 않은 링크입니다."}, status=status.HTTP_400_BAD_REQUEST)


# login, logout, tokenrefresh
class SessionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"])
    def login(self, request):
        ser = LoginSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        tokens = ser.save()

        resp = Response({"access": tokens["access"]}, status=200)
        secure = not settings.DEBUG
        refresh_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
        resp.set_cookie(
            "refresh_token",
            tokens["refresh"],
            max_age=refresh_age,
            secure=secure,
            httponly=True,
            samesite="Lax",
            path="/",
        )
        resp.set_cookie(
            "access_token",
            tokens["access"],
            max_age=refresh_age,
            secure=secure,
            httponly=True,
            samesite="Lax",
            path="/",
        )
        return resp

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        # access 블랙리스ㅡㅌ
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
        resp.delete_cookie("refresh_token")
        resp.delete_cookie("access_token")
        return resp

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

    def get(self, request):
        client_id = settings.NAVER_CLIENT_ID
        redirect_uri = settings.NAVER_REDIRECT_URI
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
