import uuid
from django.db import models
from products.models import Product
from users.models import User
from utils.models import TimestampModel


class Order(TimestampModel):
    used_point = models.IntegerField(default=0)
    order_status = models.CharField(max_length=15, default='접수 완료')
    delivery_status = models.CharField(max_length=15, default='배송 준비')
    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) # editable:관리자페이지에서 변경 불가

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='orders',  # 유저에서 참조
        null=True,
    )
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        verbose_name = '주문'
        verbose_name_plural = '주문 목록'

    def __str__(self):
            return f"Order({self.order_number})"

class OrderProduct(TimestampModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_products',
    )
    amount = models.PositiveIntegerField(null=True, blank=True, default=1)
    product = models.ForeignKey(Product, related_name='ordered_products', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'order_products'
        ordering = ['-created_at']
        verbose_name = '주문 상품'
        verbose_name_plural = '주문 상품 목록'

    def __str__(self):
        return f"OrderProduct({self.order})"

class Payment(TimestampModel):
    payment_status = models.CharField(max_length=15, null=False, blank=False, default="ready"),
    payment_method = models.CharField(max_length=15, null=False, blank=False),
    payment_amount = models.PositiveIntegerField(null=True, blank=True, default=0),
    order = models.ForeignKey(
        "Order",
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True,
    )

    class Meta:
        db_table = 'payments'
        verbose_name = '결제'
        verbose_name_plural = '결제 목록'

    def __str__(self):
        return f"Payment({self.payment_status})"