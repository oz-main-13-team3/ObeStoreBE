from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import ProductQnaListView, ProductViewSet

router = DefaultRouter()
router.register("", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
    path("<int:product_pk>/qna/", ProductQnaListView.as_view(), name="product-qna-list"),
]
