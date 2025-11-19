from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order, Payment
from orders.schemas.order_schema import OrderPreviewSchema, OrderSchema
from orders.schemas.payment_schema import PaymentSchema, TossFailSchema, TossSuccessSchema
from orders.serializers import OrderSerializer, PaymentSerializer, ReadyPaymentResponseSerializer
from orders.services.order_service import OrderService
from orders.services.payment_service import PaymentService


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff

@OrderPreviewSchema
class OrderPreview(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = OrderService.preview_order(request.user, request.data)
        return Response(data, status=status.HTTP_200_OK)

@OrderSchema
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user", "address").prefetch_related("order_products__product")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        order = OrderService.create_order(request.user, request.data)
        return Response(
            {
                "order_id": order.id,
                "order_number": str(order.order_number),
                "message": "주문이 생성되었습니다. 결제 진행 후 결제가 완료되면 장바구니가 비워집니다.",
                "pay_amount": order.total_payment,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")

    @extend_schema(exclude=True)
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE")

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()

        if order.user != request.user and not request.user.is_staff:
            return Response({"detail": "권한 없음"}, status=403)

        data = request.data or {}
        allowed_keys = {"order_status"}
        if set(data.keys()) - allowed_keys:
            return Response({"detail": "order_status만 수정할 수 있습니다."}, status=400)

        new_status = data.get("order_status")
        if new_status != "주문 취소":
            return Response({"detail": "order_status는 '주문 취소'만 허용됩니다."}, status=400)

        if Payment.objects.filter(order=order, payment_status="success").exists():
            return Response({"detail": "결제 완료 주문은 취소할 수 없습니다."}, status=409)

        if order.order_status == "주문 취소":
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=200)

        if order.order_status not in ["접수 완료"]:
            return Response(
                {"detail": f"현재 상태({order.order_status})에서는 취소할 수 없습니다."},
                status=409,
            )

        order.order_status = "주문 취소"
        order.save(update_fields=["order_status", "updated_at"])

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=200)


@PaymentSchema
class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.select_related("order", "order__user")
    http_method_names = ["get", "post"]

    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"detail": "결제 목록은 관리자만 조회할 수 있습니다."}, status=403)
        return Response(PaymentSerializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            obj = self.get_queryset().get(pk=pk)
        except Payment.DoesNotExist:
            return Response({"detail": "존재하지 않는 결제"}, status=404)
        if not (request.user.is_staff or (obj.order and obj.order.user_id == request.user.id)):
            return Response({"detail": "권한 없음"}, status=403)
        return Response(PaymentSerializer(obj).data)

    def create(self, request, *args, **kwargs):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id 누락"}, status=400)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "주문 정보 없음"}, status=404)

        data = PaymentService.ready_payment(order=order, user=request.user, request=request)
        return Response(ReadyPaymentResponseSerializer(data).data, status=200)


@TossSuccessSchema
class TossSuccessBridge(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, request):
        payment_key = request.query_params.get("paymentKey")
        order_id = request.query_params.get("orderId")
        amount_qs = request.query_params.get("amount")
        if not (payment_key and order_id and amount_qs):
            return Response({"detail": "필수 파라미터 누락"}, status=400)
        try:
            amount = int(amount_qs)
        except (TypeError, ValueError):
            return Response({"detail": "amount가 유효하지 않습니다."}, status=400)

        try:
            payment = PaymentService.confirm_payment(payment_key, order_id, amount)
        except Exception as e:
            detail = getattr(e, "detail", {"detail": str(e)})
            return Response(detail, status=400)

        order = payment.order

        front_result = getattr(settings, "FRONT_RESULT_URL", None)
        if not front_result:
            return Response(
                {
                    "status": "success",
                    "order_number": str(order.order_number),
                    "orderId": order.id,
                    "receipt_url": payment.receipt_url,
                },
                status=200,
            )

        query = urlencode(
            {
                "status": "success",
                "orderNumber": str(order.order_number),
                "orderId": order.id,
                "receiptUrl": payment.receipt_url or "",
            }
        )
        url = f"{front_result}?{query}"

        return redirect(url)


@TossFailSchema
class TossFailBridge(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        message = request.query_params.get("message")
        order_id = request.query_params.get("orderId")

        front_result = getattr(settings, "FRONT_RESULT_URL", None)
        if not front_result:
            return Response(
                {
                    "status": "fail",
                    "code": code,
                    "message": message,
                    "orderId": order_id,
                },
                status=400,
            )

        query = urlencode(
            {
                "status": "fail",
                "code": code,
                "message": message,
                "orderId": order_id,
            }
        )
        url = f"{front_result}?{query}"
        return redirect(url)