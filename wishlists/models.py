from django.db import models
from django.db.models import ForeignKey

from products.models import Product
from users.models import User
from utils.models import TimestampModel


class Wishlist(TimestampModel):
    user = ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlists')

    class Meta:
        db_table = "wishlists"
        verbose_name = "찜"
        verbose_name_plural = "찜 목록"
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_product')
        ]

    def __str__(self):
        return f"[찜] {self.user.nickname} - {self.product.product_name}"