from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orders.views import OrderViewSet, TossFailBridge, TossSuccessBridge

app_name = "orders"

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("payments/toss/success/", TossSuccessBridge.as_view(), name="payment-toss-success"),
    path("payments/toss/fail/", TossFailBridge.as_view(), name="payment-toss-fail"),
    path("", include(router.urls)),
]
