import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Model

from users.models import User
from utils.models import TimestampModel


# Create your models here.
class Order(TimestampModel):
		used_point = models.IntegerField(default=0)
		order_status = models.CharField(max_length=15, default='주문접수')
		delivery_status = models.CharField(max_length=15, default='배송준비')
		order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) #editable->관리자페이지에서 변경 불가

		user = models.ForeignKey(
				User,
				on_delete=models.CASCADE,
				related_name='orders',  # 유저에서 참조
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
				on_delete=models.SET_NULL,
				null=True,
				related_name='order_products',
		)
		amount = models.IntegerField(null=True, blank=True) #음수방지로 Positive를 넣으면 좋겠다고 생각합니다.
		product_id = models.BigIntegerField('Products.product', null=True, blank=True)

		class Meta:
				db_table = 'order_products'
				ordering = ['-created_at']
				verbose_name = '주문 상품'
				verbose_name_plural = '주문 상품 목록'

		def __str__(self):
				return f"OrderProduct({self.order})"

class payment(TimestampModel):
		payment_status = models.CharField(max_length=15, null=True, blank=True),
		payment_method = models.CharField(max_length=15, null=True, blank=True),
		payment_amount = models.IntegerField(null=True, blank=True), #결제 금액이라 defult=0 이 추가 되면 좋겠다고 생각합니다. 또한 Positive도 넣으면 좋을 것 같습니다.
		order = models.ForeignKey(
				"Order",
				on_delete=models.CASCADE,
				related_name='payments',
		)

		class Meta:
				db_table = 'payments'
				verbose_name = '결제'
				verbose_name_plural = '결제 목록'

		def __str__(self):
				return f"Payment({self.payment_status})"