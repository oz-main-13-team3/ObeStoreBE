from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orders.views import OrderPreview, OrderViewSet, PaymentViewSet, TossFailBridge, TossSuccessBridge

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("orders/preview/", OrderPreview.as_view(), name="order-preview"),

    path("", include(router.urls)),
    path("payments/toss/success/", TossSuccessBridge.as_view(), name="payment-toss-success"),
    path("payments/toss/fail/", TossFailBridge.as_view(), name="payment-toss-fail"),
]
