from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from products.views import ProductQnaViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("carts/", include("carts.urls")),
    path("products/", include("products.urls")),
    path("qna/", ProductQnaViewSet.as_view({"get": "list", "post": "create"}), name="qna-list-create"),
    path(
        "qna/<int:pk>/",
        ProductQnaViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="qna-detail",
    ),
    path("", include("orders.urls")),
    path("reviews/", include("reviews.urls")),
    # OpenAPI JSON Schema
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Redoc UI
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
