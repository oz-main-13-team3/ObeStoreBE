from datetime import datetime, timezone

from django_redis import get_redis_connection
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

BLACKLIST_PREFIX = "jwt:blacklist:"


def _redis():
    return get_redis_connection("default")


def blacklist_jti(jti: str, exp_timestamp: int):
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp_timestamp - now, 1)
    _redis().setex(f"{BLACKLIST_PREFIX}{jti}", ttl, 1)


def is_blacklisted(jti: str) -> bool:
    return _redis().get(f"{BLACKLIST_PREFIX}{jti}") is not None


class RedisBlacklistJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = None

        if header is not None:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            raise AuthenticationFailed("Invalid or expired token")

        return self.get_user(validated_token), validated_token

    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        jti = token.get("jti")
        if not jti:
            raise InvalidToken("Token has no jti claim")
        if is_blacklisted(jti):
            raise AuthenticationFailed("Token blacklisted")
        return token
