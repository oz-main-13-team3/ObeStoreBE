from django.db.models import Avg
from rest_framework import serializers

from .models import Keyword, Review, ReviewImage, ReviewKeyword


class ReviewImageSerializer(serializers.ModelSerializer):
    review_image = serializers.ImageField(use_url=True)

    class Meta:
        model = ReviewImage
        fields = ["review_image"]


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ["id", "keyword_name"]


class ReviewKeywordSerializer(serializers.ModelSerializer):
    keyword_name = serializers.CharField(source="keyword.keyword_name", read_only=True)

    class Meta:
        model = ReviewKeyword
        fields = ["keyword_name"]


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
    product_id = serializers.IntegerField(source="product.id", read_only=True)

    review_keyword = ReviewKeywordSerializer(many=True, read_only=True, source="review_keywords")
    review_image = ReviewImageSerializer(many=True, read_only=True, source="review_images")

    class Meta:
        model = Review
        fields = [
            "id",
            "review_title",
            "product_id",
            "user",
            "review_image",
            "review_keyword",
            "content",
            "created_at",
            "updated_at",
        ]
