import base64
import json

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import Truncator
from rest_framework.exceptions import PermissionDenied, ValidationError

from orders.models import Payment
from products.models import Product


class PaymentService:
    @staticmethod
    @transaction.atomic
    def ready_payment(order, user, request):
        if (order.user_id != user.id) and (not getattr(user, "is_staff", False)):
            raise PermissionDenied("권한 없음")

        if order.order_status != "접수 완료":
            raise ValidationError({"detail": "이 주문은 결제가 불가한 상태입니다."})

        payment = Payment.objects.filter(order=order, payment_status="ready").first()
        if not payment:
            payment = Payment.objects.create(
                order=order,
                payment_status="ready",
                payment_method="tosspay",
                payment_amount=order.total_payment,
                toss_order_id=f"ORD-{order.order_number}",
            )

        if getattr(settings, "USE_TOSS_BRIDGE", True):
            from django.urls import reverse

            success_url = request.build_absolute_uri(reverse("payment-toss-success"))
            fail_url = request.build_absolute_uri(reverse("payment-toss-fail"))
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

        customer_email = getattr(user, "email", "") or ""
        customer_name = getattr(user, "username", None) or getattr(user, "nickname", None) or ""
        raw_phone = getattr(user, "phone_number", "") or ""
        customer_mobile = "".join(ch for ch in raw_phone if ch.isdigit())

        return {
            "orderId": payment.toss_order_id,
            "amount": payment.payment_amount,
            "successUrl": success_url,
            "failUrl": fail_url,
            "clientKey": getattr(settings, "TOSS_CLIENT_KEY", None),
            "orderName": order_name,
            "customerEmail": customer_email,
            "customerName": customer_name,
            "customerMobilePhone": customer_mobile,
        }

    @staticmethod
    @transaction.atomic
    def confirm_payment(payment_key, order_id, amount):
        payment = Payment.objects.select_for_update().filter(toss_order_id=order_id).first()
        if not payment:
            raise ValidationError({"detail": "결제 정보 없음"})

        order = payment.order
        if amount != order.total_payment:
            raise ValidationError({"detail": "금액 불일치"})

        if payment.payment_status == "success":
            return payment

        ops = list(order.order_products.select_related("product").all())
        ids = [op.product_id for op in ops if op.product_id]
        locked = {p.id: p for p in Product.objects.select_for_update().filter(id__in=ids)}
        for op in ops:
            p = locked.get(op.product_id)
            if (not p) or (getattr(p, "product_stock", 0) < op.amount):
                raise ValidationError(
                    {"detail": "재고 부족으로 결제를 진행할 수 없습니다.", "product_id": op.product_id}
                )

        secret = settings.TOSS_SECRET_KEY
        auth = base64.b64encode((secret + ":").encode()).decode()
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
                code, msg = data.get("code"), data.get("message")
            except Exception:
                code, msg = "UNKNOWN", "승인 실패"

            payment.payment_status = "failed"
            payment.fail_code = code
            payment.fail_message = msg
            payment.save(update_fields=["payment_status", "fail_code", "fail_message", "updated_at"])

            order.order_status = "주문 실패"
            order.save(update_fields=["order_status", "updated_at"])
            raise ValidationError({"detail": "결제 승인 실패", "code": code, "message": msg})

        for op in ops:
            p = locked[op.product_id]
            p.product_stock -= op.amount
        Product.objects.bulk_update(locked.values(), ["product_stock"])

        data = resp.json()
        payment.payment_status = "success"
        payment.toss_payment_key = payment_key
        payment.receipt_url = data.get("receipt", {}).get("url")
        payment.approved_at = timezone.now()
        payment.save(update_fields=["payment_status", "toss_payment_key", "receipt_url", "approved_at", "updated_at"])

        order.order_status = "주문 완료"
        order.save(update_fields=["order_status", "updated_at"])

        return payment
