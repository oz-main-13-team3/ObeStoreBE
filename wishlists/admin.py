from django.contrib import admin
from .models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'created_at')  # 리스트에서 보일 컬럼
    list_filter = ('created_at',)  # 생성일 기준 필터
    search_fields = ('user__nickname', 'product__product_name')  # 검색 기능
    ordering = ('-created_at',)  # 최신순 정렬
