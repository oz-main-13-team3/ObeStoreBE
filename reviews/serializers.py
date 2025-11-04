from rest_framework import serializers

from products.serializer import ProductSerializer
from .models import Review, ReviewImage, ReviewKeyword, Keyword
from products.serializers import ProductSerializere


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'review', 'review_image', 'created_at']


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ["id", "keyword_name"]


class ReviewKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewKeyword
        fields = ["id", "review", "keyword"]


class ReviewSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
					"id",
					"review_title",
					"product",
					"user",
					"review_images",
					"review_keyword",
					"content",
					"created_at",
					"updated_at",
				]
