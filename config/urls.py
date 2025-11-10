from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("users/carts/", include("carts.urls")),
    path("products/", include("products.urls")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("reviews/", include("reviews.urls")),
]
