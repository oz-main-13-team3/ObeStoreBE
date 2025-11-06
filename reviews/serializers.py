from django.db.models import Avg
from rest_framework import serializers

from products.serializer import ProductSerializer

from .models import Keyword, Review, ReviewImage, ReviewKeyword


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ["id", "review", "review_image", "created_at"]


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ["id", "keyword_name"]


class ReviewKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewKeyword
        fields = ["id", "review", "keyword"]


class RatingAverageSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    average_rating = serializers.FloatField(read_only=True)

    def to_representation(self, instance):
        product_id = instance.get("product_id")
        avg_rating = Review.objects.filter(product_id=product_id).aggregate(average=Avg("rating"))["average"] or 0
        return {
            "product_id": product_id,
            "average_rating": round(avg_rating, 2),
        }


def validate_rating(value):
    if not 1 <= value <= 5:
        raise serializers.ValidationError("별점이 주어집니다.")
    return value


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
