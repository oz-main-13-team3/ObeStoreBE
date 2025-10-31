from django.db import models
from django.contrib.auth import get_user_model

from utils.models import TimestampModel


class Review(TimestampModel):
    review_title = models.CharField(max_length=50)
    content = models.TextField()
    product_id = models.ForeignKey('Product', on_delete=models.SET_NULL, related_name='product_reviews')
    user = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='user_reviews')

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        verbose_name = '리뷰'
        verbose_name_plural = '리뷰 목록'

class Keyword(models.Model):
    keyword_type = models.CharField(max_length=15)
    keyword_name = models.CharField(max_length=15, unique=True)
    keywords = models.ManyToManyField('Keyword', related_name='keywords')

    class Meta:
        db_table = 'keywords'
        ordering = ['-created_at']
        verbose_name = '키워드'
        verbose_name_plural = '키워드 목록'

class ReviewKeyword(models.Model):
    review_id = models.ForeignKey(Review, on_delete=models.SET_NULL, related_name='review_keywords')
    keyword_id = models.ForeignKey(Keyword, on_delete=models.SET_NULL, related_name='keyword_reviews')

    class Meta:
        db_table = 'review_keywords'
        ordering = ['-created_at']


class ReviewImage(TimestampModel):
    review_image = models.ImageField()
    review_id = models.ForeignKey(Review, on_delete=models.SET_NULL, related_name='review_images')

    class Meta:
        db_table = 'review_images'
        ordering = ['-created_at']
        verbose_name = '리뷰이미지'
        verbose_name_plural = '리뷰이미지 목록'
