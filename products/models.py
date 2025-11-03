from django.db import models

from utils.models import TimestampModel


class Tag(models.Model):
    tag_name = models.CharField(max_length=15, null=False, blank=False, unique=True)

    class Meta:
        db_table = "tags"
        verbose_name = "태그"
        verbose_name_plural = "태그 목록"

    def __str__(self):
        return self.tag_name


class Category(models.Model):
    category_name = models.CharField(max_length=15, null=False, blank=False, unique=True)

    class Meta:
        db_table = "categories"
        verbose_name = "카테고리"
        verbose_name_plural = "카테고리 목록"

    def __str__(self):
        return self.category_name


class Brand(models.Model):
    brand_name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    class Meta:
        db_table = "brands"
        verbose_name = "브랜드"
        verbose_name_plural = "브랜드 목록"

    def __str__(self):
        return self.brand_name


class BrandImage(TimestampModel):
    brand_image = models.ImageField(null=False, blank=False, unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name="brand_image")

    class Meta:
        db_table = "brand_images"
        verbose_name = "브랜드 이미지"
        verbose_name_plural = "브랜드 이미지 목록"

    def __str__(self):
        return f"{self.brand.brand_name} - {self.brand_id}"


class Product(TimestampModel):
    product_name = models.CharField(max_length=100, null=False, blank=False)
    product_value = models.IntegerField(null=False, blank=False)
    product_stock = models.IntegerField(null=False, blank=False)
    discount_rate = models.DecimalField(max_digits=3, decimal_places=2, null=False, blank=False, default=0)
    product_rating = models.DecimalField(max_digits=2, decimal_places=1, null=False, blank=False, default=0)
    sales = models.IntegerField(null=False, blank=False, default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name="products")

    class Meta:
        ordering = ["-created_at"]
        db_table = "products"
        verbose_name = "상품"
        verbose_name_plural = "상품목록"

    def __str__(self):
        return self.product_name


class ProductImage(TimestampModel):
    product_image = models.ImageField(null=False, blank=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="product_image")

    class Meta:
        db_table = "product_images"
        verbose_name = "상품 이미지"
        verbose_name_plural = "상품 이미지 목록"

    def __str__(self):
        return f"{self.product.product_name} - {self.product_id}"


class ProductQna(TimestampModel):
    question_type = models.CharField(max_length=15, null=False, blank=False)
    question_title = models.CharField(max_length=50, null=False, blank=False)
    question_content = models.TextField(null=False, blank=False)
    question_answer = models.TextField(null=True, blank=True)
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="product_qnas")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="qnas")

    class Meta:
        ordering = ["-created_at"]
        db_table = "product_qna"
        verbose_name = "상품 문의"
        verbose_name_plural = "상품 문의 목록"

    def __str__(self):
        return f"[{self.question_type}] {self.question_title}"
