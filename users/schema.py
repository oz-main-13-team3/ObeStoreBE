from drf_spectacular.extensions import OpenApiAuthenticationExtension


class RedisBlacklistJWTAuthExtension(OpenApiAuthenticationExtension):
    target_class = "users.auth.RedisBlacklistJWTAuthentication"
    name = "JWTAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
