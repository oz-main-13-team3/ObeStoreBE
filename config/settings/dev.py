import os

from dotenv import load_dotenv

from config.settings.base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "obestore_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "password1234"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),  # docker-compose의 서비스명
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
