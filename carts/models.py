from django.db import models

from products.models import Product
from users.models import User
from utils.models import TimestampModel


# Create your models here.
class Cart(TimestampModel):
		user = models.OneToOneField(
				User,
				on_delete=models.CASCADE,
				related_name='cart',  # 유저에서 참조
				primary_key=True,  #ERD 식별로 되어있음
		)

		class Meta:
				db_table = 'carts'
				ordering = ['-created_at']
				verbose_name = '장바구니'
				verbose_name_plural = '장바구니 목록'

		def __str__(self):
				return f"Cart({self.user}님)" # 추후 수정 부탁드립니다.


class CartItem(TimestampModel):
		amount = models.IntegerField(default=0)
		cart = models.ForeignKey(
				Cart,
				on_delete=models.CASCADE,
				related_name='items',
		)
		product = models.ForeignKey(
				Product,
				on_delete=models.CASCADE,  # 장바구니와 상품에서 참조
				related_name='cart_items',
		)

		class Meta:
				db_table = 'cart_items'
				ordering = ['-created_at']
				verbose_name = '장바구니 상품'
				verbose_name_plural = '장바구니 상품 목록'

		def __str__(self):
				return f"CartItem({self.product} 상품 {self.amount} 개)"  # 추후 수정 부탁드립니다.
