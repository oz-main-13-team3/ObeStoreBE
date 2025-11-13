import ast
import os

from dotenv import load_dotenv

from config.settings.base import *  # noqa

DEBUG = False
raw_hosts = os.getenv("ALLOWED_HOSTS", "[]")
ALLOWED_HOSTS = ast.literal_eval(raw_hosts)

load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "obestore_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "password1234"),
        "HOST": os.getenv("DB_HOST", "localhost"),  # docker-compose의 서비스명
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa

# DJANGO STORAGES
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
            "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME"),
            "region_name": os.getenv("AWS_S3_REGION_NAME"),
            "location": "media",
            "default_acl": "public-read",
            "querystring_auth": False,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
            "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME"),
            "region_name": os.getenv("AWS_S3_REGION_NAME"),
            "location": "static",
            "default_acl": "public-read",
            "querystring_auth": False,
        },
    },
}

# AWS Credentials
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_S3_SIGNATURE_VERSION = "s3v4"

AWS_S3_CUSTOM_DOMAIN = f"{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.{os.getenv("AWS_S3_REGION_NAME")}.amazonaws.com"

STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

# CSRF
raw_csrf_trusted_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "[]")
CSRF_TRUSTED_ORIGINS = ast.literal_eval(raw_csrf_trusted_origins)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
