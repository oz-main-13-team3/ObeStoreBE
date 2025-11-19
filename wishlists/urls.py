# wishlist/urls.py
from django.urls import path

from .views import WishlistViewSet

wishlist = WishlistViewSet.as_view({"get": "list", "post": "create"})
wishlist_detail = WishlistViewSet.as_view({"delete": "destroy"})

urlpatterns = [
    path("users/me/wishlist/", wishlist, name="wishlist-list"),
    path("users/me/wishlist/<int:pk>/", wishlist_detail, name="wishlist-delete"),
]
