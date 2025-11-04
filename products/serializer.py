from rest_framework import serializers

from products.models import Product, ProductQna


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.category_name", read_only=True)
    tag_name = serializers.CharField(source="tag.tag_name", read_only=True)
    brand_name = serializers.CharField(source="brand.brand_name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "product_value",
            "product_stock",
            "discount_rate",
            "product_rating",
            "created_at",
            "updated_at",
            "category_id",
            "category_name",
            "tag_id",
            "tag_name",
            "brand_id",
            "brand_name",
        ]


class ProductQnaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductQna
        fields = ["product", "question_type", "question_title", "question_content"]
        extra_kwargs = {
            "product": {"required": True},
            "question_type": {"required": True},
            "question_title": {"required": True},
            "question_content": {"required": True},
        }

    def create(self, validated_data):
        user = self.context["request"].user
        return ProductQna.objects.create(user=user, **validated_data)


class ProductQnaSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    product_name = serializers.CharField(source="product.product_name", read_only=True)

    class Meta:
        model = ProductQna
        fields = [
            "id",
            "product_name",
            "username",
            "question_type",
            "question_title",
            "question_content",
            "question_answer",
            "created_at",
            "updated_at",
        ]
