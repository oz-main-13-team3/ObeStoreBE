from django.db import models

from utils.models import TimestampModel
from utils.upload_paths import general_upload_to


class Keyword(models.Model):
    KEYWORD_TYPE_CHOICES = (("positive", "긍정"), ("neutral", "중립"), ("negative", "부정"))
    keyword_type = models.CharField(max_length=15, choices=KEYWORD_TYPE_CHOICES)
    keyword_name = models.CharField(max_length=15, unique=True)

    class Meta:
        db_table = "keywords"
        verbose_name = "키워드"
        verbose_name_plural = "키워드 목록"

    def __str__(self):
        return f"[{self.keyword_type}] {self.keyword_name}"


class Review(TimestampModel):
    review_title = models.CharField(max_length=50)
    content = models.TextField(null=False, blank=False)
    rating = models.PositiveSmallIntegerField(default=5)
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, related_name="product_reviews", null=True
    )
    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, related_name="user_reviews", null=True)
    keywords = models.ManyToManyField("reviews.Keyword", through="ReviewKeyword", related_name="reviews")

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        verbose_name = "리뷰"
        verbose_name_plural = "리뷰 목록"


class ReviewKeyword(models.Model):
    review = models.ForeignKey("reviews.Review", on_delete=models.CASCADE, related_name="review_keywords")
    keyword = models.ForeignKey("reviews.Keyword", on_delete=models.CASCADE, related_name="keyword_reviews")

    class Meta:
        db_table = "review_keywords"
        constraints = [models.UniqueConstraint(fields=["review", "keyword"], name="unique_review_keyword")]


class ReviewImage(TimestampModel):
    upload_folder = "reviews"
    upload_fk = "review"
    review_image = models.ImageField(upload_to=general_upload_to)
    review = models.ForeignKey("reviews.Review", on_delete=models.SET_NULL, related_name="review_images", null=True)

    class Meta:
        db_table = "review_images"
        ordering = ["-created_at"]
        verbose_name = "리뷰이미지"
        verbose_name_plural = "리뷰이미지 목록"
