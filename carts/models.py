from django.db import models

from products.models import Product
from users.models import User
from utils.models import TimestampModel


class Cart(TimestampModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart",  # 유저에서 참조
    )

    class Meta:
        db_table = "carts"
        ordering = ["-created_at"]
        verbose_name = "장바구니"
        verbose_name_plural = "장바구니 목록"

    def __str__(self):
        return f"{self.user.nickname}의 카트"


class CartItem(TimestampModel):
    amount = models.IntegerField(default=0)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        related_name="items",
        null=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,  # 장바구니와 상품에서 참조
        related_name="cart_items",
        null=True,
    )

    class Meta:
        db_table = "cart_items"
        ordering = ["-created_at"]
        verbose_name = "장바구니 상품"
        verbose_name_plural = "장바구니 상품 목록"
        unique_together = ("cart", "product")

    def __str__(self):
        return f"[{self.cart.user.nickname} 카트] {self.product.product_name} 상품 | {self.amount} 개"
