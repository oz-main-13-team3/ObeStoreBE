import uuid

from django.db import models

from products.models import Product
from users.models import User
from utils.models import TimestampModel

from .choices import DeliveryStatus, OrderStatus, PaymentMethod, PaymentStatus


class Order(TimestampModel):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="orders",  # 유저에서 참조
        null=True,
    )
    address = models.ForeignKey(
        "users.Address",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        verbose_name="배송지",
    )
    subtotal = models.PositiveIntegerField(default=0, verbose_name="상품 총합")
    discount_amount = models.PositiveIntegerField(default=0, verbose_name="할인 금액")
    delivery_amount = models.PositiveIntegerField(default=0, verbose_name="배송비")
    delivery_request = models.CharField(max_length=100, null=True, blank=True, verbose_name="배송 시 요청사항")
    total_payment = models.PositiveIntegerField(default=0, verbose_name="최종 결제 금액")
    used_point = models.IntegerField(default=0, verbose_name="사용된 적립금")
    order_status = models.CharField(max_length=15, choices=OrderStatus, default="접수 완료", verbose_name="주문상태")
    delivery_status = models.CharField(
        max_length=15, choices=DeliveryStatus, default="배송 준비", verbose_name="배송상태"
    )

    order_number = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, verbose_name="주문번호(노출용)"
    )  # editable:관리자페이지에서 변경 불가

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = "주문"
        verbose_name_plural = "주문 목록"

    def __str__(self):
        return f"Order({self.order_number})"


class OrderProduct(TimestampModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_products", verbose_name="주문")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_products",
        verbose_name="상품",
    )
    amount = models.PositiveIntegerField(null=True, blank=True, default=1, verbose_name="상품수량")
    price = models.PositiveIntegerField(verbose_name="상품 주문 당시 가격")  # <- 상품의 가격 변동이 있을 수 있어서
    total_price = models.PositiveIntegerField(verbose_name="상품 총 금액")

    class Meta:
        db_table = "order_products"
        ordering = ["-created_at"]
        verbose_name = "주문 상품"
        verbose_name_plural = "주문 상품 목록"

    def __str__(self):
        return f"OrderProduct({self.order})"


class Payment(TimestampModel):
    order = models.ForeignKey(
        "Order",
        on_delete=models.SET_NULL,
        related_name="payments",
        null=True,
        verbose_name="주문번호",
    )
    payment_status = models.CharField(
        max_length=15,
        choices=PaymentStatus,
        null=False,
        blank=False,
        default="ready",
        verbose_name="결제상태",
    )
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethod,
        null=False,
        blank=False,
        default="tosspay",
        verbose_name="결제수단",
    )

    payment_amount = models.PositiveIntegerField(null=True, blank=True, default=0, verbose_name="결제금액")

    # 토스 연동 필드
    toss_order_id = models.CharField(max_length=100, db_index=True, unique=True)
    toss_payment_key = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    receipt_url = models.URLField(null=True, blank=True)

    approved_at = models.DateTimeField(null=True, blank=True)
    fail_code = models.CharField(max_length=50, null=True, blank=True)
    fail_message = models.CharField(max_length=255, null=True, blank=True)

    idempotency_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    class Meta:
        db_table = "payments"
        verbose_name = "결제"
        verbose_name_plural = "결제 목록"

    def __str__(self):
        return f"Payment({self.payment_status})"
