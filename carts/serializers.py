from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.product_name")
    price = serializers.ReadOnlyField(source="product.product_value")
    total_price = serializers.SerializerMethodField()

    product_card_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_name",
            "price",
            "total_price",
            "created_at",
            "updated_at",
            "amount",
            "cart",
            "product",
            "product_card_image"
        ]
        read_only_fields = ["cart"]

    @extend_schema_field(str)
    def get_product_card_image(self, obj):
        images = obj.product.product_images.all()
        if not images.exists():
            return None
        return images.first().product_card_image.url

    @extend_schema_field(serializers.IntegerField())
    def get_total_price(self, obj):
        if not obj.product:
            return 0
        return obj.product.product_value * obj.amount


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ["user"]

    @extend_schema_field(serializers.IntegerField())
    def get_total_price(self, obj):
        total = 0
        for item in obj.items.all():
            if item.product:
                total += item.product.product_value * item.amount
        return total
