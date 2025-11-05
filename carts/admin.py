from django.contrib import admin

from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__email", "user__nickname")
    ordering = ("-created_at",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart_user", "product_name", "amount", "created_at")
    search_fields = ("cart__user__nickname", "product__product_name")
    ordering = ("-created_at",)

    def cart_user(self, obj):
        return obj.cart.user.nickname if obj.cart and obj.cart.user else "삭제된 사용자"

    cart_user.short_description = "유저 닉네임"

    def product_name(self, obj):
        return obj.product.product_name if obj.product else "삭제된 상품"

    product_name.short_description = "상품명"
