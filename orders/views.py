import base64
import json

import requests
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.models import CartItem
from orders.models import Order, Payment
from orders.serializers import OrderSerializer
from products.models import Product
from users.models import Address
from users.services.points import get_point_balance


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


@extend_schema_view(
    list=extend_schema(
        summary="주문 목록",
        description="로그인한 사용자의 주문 목록을 조회합니다.",
        responses=OrderSerializer(many=True),
        tags=["orders"],
    ),
    retrieve=extend_schema(
        summary="주문 단건 조회",
        description="로그인한 사용자의 주문 상세를 조회합니다.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, "path")],
        responses=OrderSerializer,
        tags=["orders"],
    ),
    create=extend_schema(
        summary="주문 생성",
        description="장바구니 기반으로 주문을 생성합니다.",
        request=OrderSerializer,
        responses={
            201: inline_serializer(
                name="OrderCreateResponse",
                fields={
                    "order_number": serializers.CharField(),
                    "message": serializers.CharField(),
                    "pay_amount": serializers.IntegerField(),
                },
            )
        },
        tags=["orders"],
    ),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(
        summary="주문 취소(PATCH 전용)",
        description="주문 상태를 '주문 취소'로 변경만 허용합니다. 결제 완료 주문은 취소 불가.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, "path")],
        request=inline_serializer(
            name="OrderCancelPatch",
            fields={"order_status": serializers.ChoiceField(choices=["주문 취소"])},
        ),
        responses=OrderSerializer,
        tags=["orders"],
    ),
    destroy=extend_schema(exclude=True),
)
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
        user = request.user

        address_id = request.data.get("address")
        if not address_id:
            raise ValidationError({"address": "배송지 ID를 반드시 전달해야 합니다."})

        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            raise NotFound("해당 배송지를 찾을 수 없습니다.")
        if address.user != user:
            raise ValidationError({"address": "본인 주소만 선택할 수 있습니다."})

        cart_items = CartItem.objects.filter(cart__user=user).select_related("product")
        if not cart_items.exists():
            raise ValidationError({"cart": "장바구니가 비어 있습니다."})

        used_point = int(request.data.get("used_point") or 0)
        user_point = get_point_balance(user)
        if used_point > user_point:
            raise ValidationError({"used_point": f"보유 포인트({user_point})보다 많이 사용할 수 없습니다."})

        product_ids = [item.product_id for item in cart_items]
        products_qs = Product.objects.select_for_update().filter(id__in=product_ids)
        products_map = {p.id: p for p in products_qs}

        order_products_payload = []
        subtotal = 0

        for item in cart_items:
            product = products_map.get(item.product_id)
            if not product:
                raise ValidationError({"product": f"상품(id={item.product_id}) 정보를 찾을 수 없습니다."})
            qty = item.amount

            if hasattr(product, "product_stock") and product.product_stock < qty:
                raise ValidationError(
                    {"stock": f"'{product.product_stock}' 재고 부족 (보유: {product.product_stock}, 요청: {qty})"}
                )

            price = product.product_value
            total_price = price * qty
            subtotal += total_price

            order_products_payload.append(
                {
                    "product": product.id,
                    "amount": qty,
                }
            )

        discount_amount = int(request.data.get("discount_amount") or 0)
        delivery_amount = int(request.data.get("delivery_amount") or 0)
        total_payment = subtotal - discount_amount - used_point + delivery_amount
        if total_payment < 0:
            raise ValidationError({"total_payment": "결제 금액이 0보다 작을 수 없습니다."})

        payload = {
            "address": address.id,
            "discount_amount": discount_amount,
            "delivery_amount": delivery_amount,
            "used_point": used_point,
            "order_products": order_products_payload,
        }

        serializer = self.get_serializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        order = serializer.save(user=user, order_status="접수 완료")
        return Response(
            {
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

    @extend_schema(
        summary="결제 준비",
        description="Toss 결제 페이지로 이동하기 전 필요한 값을 생성/반환합니다.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, "path")],
        request=None,
        responses=inline_serializer(
            name="PaymentReadyResponse",
            fields={
                "orderId": serializers.CharField(),
                "amount": serializers.IntegerField(),
                "successUrl": serializers.URLField(),
                "failUrl": serializers.URLField(),
                "clientKey": serializers.CharField(allow_null=True, required=False),
                "orderName": serializers.CharField(),
                "customerEmail": serializers.CharField(allow_blank=True, required=False),
                "customerName": serializers.CharField(allow_blank=True, required=False),
                "customerMobilePhone": serializers.CharField(allow_blank=True, required=False),
            },
        ),
        tags=["orders"],
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def ready_payment(self, request):
        order = self.get_object()
        if order.user != request.user and not request.user.is_staff:
            return Response({"detail": "권한 없음"}, status=403)

        if order.order_status != "접수 완료":
            return Response({"detail": "이 주문은 결제가 불가한 상태입니다."}, status=400)

        payment = Payment.objects.filter(order=order, payment_status="ready").first()
        if not payment:
            toss_order_id = f"ORD-{order.order_number}"
            payment = Payment.objects.create(
                order=order,
                payment_status="ready",
                payment_method="tosspay",
                payment_amount=order.total_payment,
                toss_order_id=toss_order_id,
            )

        if getattr(settings, "USE_TOSS_BRIDGE", True):
            # 테스트용
            success_url = request.build_absolute_uri(reverse("orders:payment-toss-success"))
            fail_url = request.build_absolute_uri(reverse("orders:payment-toss-fail"))
        else:
            success_url = settings.FRONT_SUCCESS_URL
            fail_url = settings.FRONT_FAIL_URL

        items = list(order.order_products.select_related("product").all())
        if items:
            first_name = items[0].product.product_name if items[0].product else "상품"
            first_name = Truncator(first_name).chars(30)
            cnt = len(items) - 1
            order_name = f"{first_name} 외 {cnt}건" if cnt > 0 else first_name
        else:
            order_name = "주문"

        u = order.user
        customer_email = getattr(u, "email", "") or ""
        customer_name = getattr(u, "username", None) or getattr(u, "nickname", None) or ""
        raw_phone = getattr(u, "phone_number", "") or ""
        customer_mobile = "".join(ch for ch in raw_phone if ch.isdigit())

        return Response(
            {
                "orderId": payment.toss_order_id,
                "amount": payment.payment_amount,
                "successUrl": success_url,
                "failUrl": fail_url,
                "clientKey": getattr(settings, "TOSS_CLIENT_KEY", None),
                "orderName": order_name,
                "customerEmail": customer_email,
                "customerName": customer_name,
                "customerMobilePhone": customer_mobile,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="결제 승인",
        description="서버에서 Toss confirm 호출",
        request=inline_serializer(
            name="ApproveRequest",
            fields={
                "orderId": serializers.CharField(),
                "paymentKey": serializers.CharField(),
                "amount": serializers.IntegerField(),
            },
        ),
        responses=inline_serializer(
            name="ApproveResponse",
            fields={
                "order_number": serializers.CharField(),
                "payment_id": serializers.IntegerField(),
                "status": serializers.CharField(),
                "receipt_url": serializers.CharField(allow_null=True, required=False),
            },
        ),
        tags=["orders"],
    )
    @action(detail=False, methods=["post"], url_path="approve", permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def approve_payment(self, request):
        order_id = request.data.get("orderId")
        payment_key = request.data.get("paymentKey")
        try:
            amount = int(request.data.get("amount", 0))
        except (TypeError, ValueError):
            return Response({"detail": "amount가 유효하지 않습니다."}, status=400)

        payment = Payment.objects.select_for_update().filter(toss_order_id=order_id).first()
        if not payment:
            return Response({"detail": "결제 정보 없음"}, status=404)

        order = payment.order
        if order.user != request.user and not request.user.is_staff:
            return Response({"detail": "권한 없음"}, status=403)

        if amount != order.total_payment:
            return Response({"detail": "금액 불일치"}, status=400)

        if payment.payment_status == "success":
            return Response(
                {
                    "detail": "이미 승인됨",
                    "order_number": str(order.order_number),
                    "payment_id": payment.id,
                    "receipt_url": payment.receipt_url,
                },
                status=200,
            )

        ops = list(order.order_products.select_related("product").all())
        product_ids = [op.product_id for op in ops if op.product_id]

        locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

        for op in ops:
            p = locked_products.get(op.product_id)
            if (not p) or (getattr(p, "product_stock", 0) < op.amount):
                return Response(
                    {"detail": "재고 부족으로 결제를 진행할 수 없습니다.", "product_id": op.product_id},
                    status=409,
                )

        secret_key = settings.TOSS_SECRET_KEY
        auth = base64.b64encode((secret_key + ":").encode()).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
        body = {"paymentKey": payment_key, "orderId": order_id, "amount": amount}

        resp = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            data=json.dumps(body),
            headers=headers,
            timeout=10,
        )

        if resp.status_code != 200:
            try:
                data = resp.json()
                code = data.get("code")
                msg = data.get("message")
            except Exception:
                code, msg = "UNKNOWN", "승인 실패"

            payment.payment_status = "failed"
            payment.fail_code = code
            payment.fail_message = msg
            payment.save(update_fields=["payment_status", "fail_code", "fail_message", "updated_at"])

            order.order_status = "주문 실패"
            order.save(update_fields=["order_status", "updated_at"])

            return Response({"detail": "결제 승인 실패", "code": code, "message": msg}, status=400)

        for op in ops:
            p = locked_products[op.product_id]
            p.product_stock = p.product_stock - op.amount
        Product.objects.bulk_update(locked_products.values(), ["product_stock"])

        data = resp.json()
        payment.payment_status = "success"
        payment.toss_payment_key = payment_key
        payment.receipt_url = data.get("receipt", {}).get("url")
        payment.approved_at = timezone.now()
        payment.save(update_fields=["payment_status", "toss_payment_key", "receipt_url", "approved_at", "updated_at"])
        order.order_status = "주문 완료"
        order.save(update_fields=["order_status", "updated_at"])
        return Response(
            {
                "order_number": str(order.order_number),
                "payment_id": payment.id,
                "status": "success",
                "receipt_url": payment.receipt_url,
            },
            status=200,
        )


class TossSuccessBridge(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Toss 결제 성공 브리지",
        description="Toss 결제 완료 후 프론트 -> 백엔드로 리다이렉트 할 때 사용하는 브리지 엔드포인트",
        tags=["payments"],
        parameters=[
            OpenApiParameter(
                name="paymentKey",
                type=OpenApiTypes.STR,
                location="query",
                required=True,
                description="Toss에서 redirect 시 넘겨주는 결제 키",
            ),
            OpenApiParameter(
                name="orderId",
                type=OpenApiTypes.STR,
                location="query",
                required=True,
                description="우리가 생성해 둔 결제용 주문ID (예: ORD-xxxx)",
            ),
            OpenApiParameter(
                name="amount",
                type=OpenApiTypes.INT,
                location="query",
                required=True,
                description="결제 금액(검증용)",
            ),
        ],
        responses={
            200: inline_serializer(
                name="TossSuccessResponse",
                fields={
                    "status": serializers.CharField(),  # "success"
                    "order_number": serializers.CharField(),  # 내부 주문번호(표시용)
                    "receipt_url": serializers.CharField(allow_null=True, required=False),
                },
            ),
            400: inline_serializer(
                name="TossSuccessBadRequest",
                fields={"detail": serializers.CharField()},
            ),
            404: inline_serializer(
                name="TossSuccessNotFound",
                fields={"detail": serializers.CharField()},
            ),
            409: inline_serializer(
                name="TossSuccessConflict",
                fields={"detail": serializers.CharField(), "product_id": serializers.IntegerField(required=False)},
            ),
        },
    )
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

        payment = Payment.objects.select_for_update().filter(toss_order_id=order_id).first()
        if not payment:
            return Response({"detail": "결제 정보 없음"}, status=404)

        order = payment.order
        if amount != order.total_payment:
            return Response({"detail": "금액 불일치"}, status=400)

        if payment.payment_status == "success":
            return Response({"detail": "이미 승인됨", "receipt_url": payment.receipt_url}, status=200)

        ops = list(order.order_products.select_related("product").all())
        product_ids = [op.product_id for op in ops if op.product_id]

        locked_products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

        for op in ops:
            p = locked_products.get(op.product_id)
            if (not p) or (getattr(p, "product_stock", 0) < op.amount):
                return Response(
                    {"detail": "재고 부족으로 결제를 진행할 수 없습니다.", "product_id": op.product_id},
                    status=409,
                )

        secret_key = settings.TOSS_SECRET_KEY
        auth = base64.b64encode((secret_key + ":").encode()).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
        body = {"paymentKey": payment_key, "orderId": order_id, "amount": amount}

        resp = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm", data=json.dumps(body), headers=headers, timeout=10
        )

        if resp.status_code != 200:
            try:
                data = resp.json()
                code, msg = data.get("code"), data.get("message")
            except Exception:
                code, msg = "UNKNOWN", "승인 실패"

            payment.payment_status = "failed"
            payment.fail_code = code
            payment.fail_message = msg
            payment.save(update_fields=["payment_status", "fail_code", "fail_message", "updated_at"])

            order.order_status = "주문 실패"
            order.save(update_fields=["order_status", "updated_at"])
            return Response({"detail": "결제 승인 실패", "code": code, "message": msg}, status=400)

        for op in ops:
            p = locked_products[op.product_id]
            p.product_stock = p.product_stock - op.amount
        Product.objects.bulk_update(locked_products.values(), ["product_stock"])

        data = resp.json()
        payment.payment_status = "success"
        payment.toss_payment_key = payment_key
        payment.receipt_url = data.get("receipt", {}).get("url")
        payment.approved_at = timezone.now()
        payment.save(update_fields=["payment_status", "toss_payment_key", "receipt_url", "approved_at", "updated_at"])

        order.order_status = "주문 완료"
        order.save(update_fields=["order_status", "updated_at"])

        return Response(
            {
                "status": "success",
                "order_number": str(order.order_number),
                "receipt_url": payment.receipt_url,
            },
            status=200,
        )


class TossFailBridge(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Toss 결제 실패 브리지",
        description="Toss 결제 실패/취소 시 프론트엔드가 실패 정보를 백엔드로 전달하는 브리지 엔드포인트",
        tags=["payments"],
        parameters=[
            OpenApiParameter(
                name="code",
                type=OpenApiTypes.STR,
                location="query",
                required=False,
                description="Toss 실패 코드",
            ),
            OpenApiParameter(
                name="message",
                type=OpenApiTypes.STR,
                location="query",
                required=False,
                description="Toss 실패 메시지",
            ),
            OpenApiParameter(
                name="orderId",
                type=OpenApiTypes.STR,
                location="query",
                required=False,
                description="우리가 생성해 둔 결제용 주문ID (있다면 전달)",
            ),
        ],
        responses={
            400: inline_serializer(
                name="TossFailResponse",
                fields={
                    "status": serializers.CharField(),  # "fail"
                    "code": serializers.CharField(allow_null=True, required=False),
                    "message": serializers.CharField(allow_null=True, required=False),
                    "orderId": serializers.CharField(allow_null=True, required=False),
                },
            )
        },
    )
    def get(self, request):
        return Response(
            {
                "status": "fail",
                "code": request.query_params.get("code"),
                "message": request.query_params.get("message"),
                "orderId": request.query_params.get("orderId"),
            },
            status=400,
        )
