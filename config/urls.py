from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("users/carts/", include("carts.urls")),
    path("products/", include("products.urls")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("reviews/", include("reviews.urls")),
    # OpenAPI JSON Schema
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Redoc UI
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
