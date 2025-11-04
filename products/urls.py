from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from products.views import ProductQnaViewSet, ProductViewSet

router = DefaultRouter()
router.register("", ProductViewSet, basename="product")

# Nested router: /products/{product_id}/qna/
products_router = NestedDefaultRouter(router, "", lookup="product")
products_router.register("qna", ProductQnaViewSet, basename="product-qna")

urlpatterns = router.urls + products_router.urls
