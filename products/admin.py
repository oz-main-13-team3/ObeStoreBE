from django.contrib import admin

from products.models import Brand, BrandImage, Category, Product, ProductImage, Tag


# ProductImage를 Product 안에서 편집할 수 있도록 Inline 정의
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # 처음 보여줄 빈 이미지 폼 개수
    # 필수: FK가 Product로 연결되어 있어야 함


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


class BrandImageInline(admin.TabularInline):
    model = BrandImage
    extra = 1


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    inlines = [BrandImageInline]


@admin.register(BrandImage)
class BrandImageAdmin(admin.ModelAdmin):
    pass
