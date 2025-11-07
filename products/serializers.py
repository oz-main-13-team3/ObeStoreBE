from rest_framework import serializers

from products.models import BrandImage, Product, ProductImage, ProductQna


class ProductImageSerializer(serializers.ModelSerializer):
    product_card_image = serializers.ImageField(use_url=True)
    product_explain_image = serializers.ImageField(use_url=True)

    class Meta:
        model = ProductImage
        fields = [
            "product_card_image",
            "product_explain_image",
        ]


class BrandImageSerializer(serializers.ModelSerializer):
    brand_image = serializers.ImageField(use_url=True)

    class Meta:
        model = BrandImage
        fields = ["brand_image"]


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.category_name", read_only=True)
    tag_name = serializers.CharField(source="tag.tag_name", read_only=True)
    brand_name = serializers.CharField(source="brand.brand_name", read_only=True)

    dc_value = serializers.SerializerMethodField()

    product_image = ProductImageSerializer(many=True, read_only=True, source="product_images")
    brand_image = BrandImageSerializer(many=True, read_only=True, source="brand.brand_images")

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "product_value",
            "product_stock",
            "discount_rate",
            "product_rating",
            "dc_value",
            "created_at",
            "updated_at",
            "category_id",
            "category_name",
            "tag_id",
            "tag_name",
            "brand_id",
            "brand_name",
            "product_image",
            "brand_image",
        ]

    def get_dc_value(self, obj):
        return int(obj.product_value * (1 - obj.discount_rate))


class ProductDetailSerializer(ProductListSerializer):
    reviews = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["reviews"]

    def get_reviews(self, obj):
        from reviews.serializers import ReviewSerializer  # 순환 참조 방지

        queryset = obj.product_reviews.all()
        return ReviewSerializer(queryset, many=True, context=self.context).data


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
