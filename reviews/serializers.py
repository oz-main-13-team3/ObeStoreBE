from rest_framework import serializers

from products.serializer import ProductSerializer
from .models import Review, ReviewImage, ReviewKeyword, Keyword
from products.models import Product
from products.serializers import ProductSerializere


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'review', 'review_image', 'created_at']


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = "__all__"


class ReviewKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewKeyword
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Review
        fields = "__all__"
