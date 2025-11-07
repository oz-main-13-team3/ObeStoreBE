from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("api/", include("carts.urls")),  # 추후 이름 수정 예정
    path("products/", include("products.urls")),
    path("api/users/", include("users.urls")),
    path("api/orders/", include("orders.urls")),
    path("reviews/", include("reviews.urls")),
]
