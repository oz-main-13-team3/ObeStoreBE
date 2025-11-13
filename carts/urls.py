from rest_framework.routers import DefaultRouter

from .views import CartItemViewSet, CartViewSet

router = DefaultRouter()
router.register(r"", CartViewSet, basename="cart")
router.register(r"items", CartItemViewSet, basename="cart-item")

urlpatterns = router.urls
