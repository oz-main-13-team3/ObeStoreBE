
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path('api/', include('carts.urls')), # 추후 이름 수정 예정
    path("products/", include("products.urls")),
]
