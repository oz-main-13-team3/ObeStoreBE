from rest_framework import serializers

from products.models import Product


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
