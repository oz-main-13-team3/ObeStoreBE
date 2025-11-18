from django.db.models import Avg
from drf_spectacular.utils import extend_schema_field
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
    nickname = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    review_keyword = ReviewKeywordSerializer(many=True, read_only=True, source="review_keywords")
    review_image = ReviewImageSerializer(many=True, read_only=True, source="review_images")

    class Meta:
        model = Review
        fields = [
            "id",
            "review_title",
            "product",
			"product_name",
            "nickname",
            "review_image",
            "review_keyword",
            "content",
            "rating",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(str)
    def get_nickname(self, obj):
        return getattr(obj.user, "nickname", None)

    @extend_schema_field(str)
    def get_product_name(self, obj):
        return getattr(obj.product, "product_name", None)

class ReviewCreateSerializer(serializers.ModelSerializer):
    keyword_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Review
        fields = [
            "review_title",
            "content",
            "rating",
            "product",
            "keyword_ids",
        ]

    def create(self, validated_data):
        keyword_ids = validated_data.pop("keyword_ids", [])
        review = Review.objects.create(**validated_data)

        if keyword_ids:
            for kid in keyword_ids:
                ReviewKeyword.objects.create(
                    review=review,
                    keyword_id=kid
                )

        return review

    def update(self, instance, validated_data):
        keyword_ids = validated_data.pop("keyword_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if keyword_ids is not None:
            instance.reviewkeyword_set.all().delete()
            for kid in keyword_ids:
                ReviewKeyword.objects.create(
                    review=instance,
                    keyword_id=kid
                )

        return instance