from django.db import models

from utils.models import TimestampModel


class Keyword(models.Model):
    keyword_type = models.CharField(max_length=15)
    keyword_name = models.CharField(max_length=15, unique=True)

    class Meta:
        db_table = "keywords"
        verbose_name = "키워드"
        verbose_name_plural = "키워드 목록"


class Review(TimestampModel):
    review_title = models.CharField(max_length=50)
    content = models.TextField(null=False, blank=False)
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, related_name="product_reviews", null=True
    )
    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, related_name="user_reviews", null=True)
    keywords = models.ManyToManyField(Keyword, through="ReviewKeyword", related_name="reviews")

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        verbose_name = "리뷰"
        verbose_name_plural = "리뷰 목록"


class ReviewKeyword(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="review_keywords")
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE, related_name="keyword_reviews")

    class Meta:
        db_table = "review_keywords"
        constraints = [models.UniqueConstraint(fields=["review", "keyword"], name="unique_review_keyword")]


class ReviewImage(TimestampModel):
    review_image = models.ImageField(null=False, blank=False)
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, related_name="review_images", null=True)

    class Meta:
        db_table = "review_images"
        ordering = ["-created_at"]
        verbose_name = "리뷰이미지"
        verbose_name_plural = "리뷰이미지 목록"
