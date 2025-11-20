from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from products.models import BrandImage, Product, ProductImage, ProductQna
from wishlists.models import Wishlist


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

    wishes = serializers.SerializerMethodField()
    is_wished = serializers.SerializerMethodField()

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
            "wishes",
            "is_wished"
        ]

    @extend_schema_field(int)
    def get_dc_value(self, obj):
        if obj.discount_rate in (None, 0):
            return obj.product_value

        try:
            rate = float(obj.discount_rate)
            return int(obj.product_value * (1 - rate))
        except Exception:
            return obj.product_value

    def get_wishes(self, obj):
        return Wishlist.objects.filter(product=obj).count()

    def get_is_wished(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return Wishlist.objects.filter(product=obj, user=user).exists()


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
    def get_username(self, obj):
        return getattr(obj.user, "username", None)

    def get_product_name(self, obj):
        return getattr(obj.product, "product_name", None)