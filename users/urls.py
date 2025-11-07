from django.urls import path

from .views import NaverCallbackView, NaverLoginView, SessionViewSet, UsersViewSet

users = UsersViewSet.as_view
session = SessionViewSet.as_view

urlpatterns = [
    path("users/signup", users({"post": "signup"}), name="signup"),
    path("users/me", users({"get": "me", "patch": "me", "delete": "me"}), name="me"),
    path("users/email/verify", users({"get": "email_verify"}), name="email_verify"),
    path("login", session({"post": "login"}), name="login"),
    path("logout", session({"post": "logout"}), name="logout"),
    path("token/refresh", session({"post": "token_refresh"}), name="token_refresh"),
    path(
        "users/me/address",
        users({"get": "address", "post": "address", "patch": "address", "delete": "address"}),
        name="me_address",
    ),
    path("users/me/points", users({"get": "points"}), name="me_points"),
    path("users/me/points/balance", users({"get": "points_balance"}), name="me_points_balance"),
    path("oauth/naver/login/", NaverLoginView.as_view(), name="naver_login"),
    path("oauth/naver/callback/", NaverCallbackView.as_view(), name="naver_callback"),
]
