from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from orders.services.order_service import OrderService

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.product_name")
    price = serializers.ReadOnlyField(source="product.product_value")
    discount_amount = serializers.SerializerMethodField()
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
            "discount_amount",
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

    def get_discount_amount(self, obj):
        return int(obj.product.product_value * obj.product.discount_rate)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    delivery_amount = serializers.SerializerMethodField()
    total_payment = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = "__all__"
        read_only_fields = ["user"]

    def get_cart_preview(self, obj):
        data = {"cart_item_ids": [item.id for item in obj.items.all()]}
        return OrderService.preview_order(obj.user, data)

    def get_subtotal(self, obj):
        return self.get_cart_preview(obj)["subtotal"]

    def get_discount_amount(self, obj):
        return self.get_cart_preview(obj)["discount_amount"]

    def get_delivery_amount(self, obj):
        return self.get_cart_preview(obj)["delivery_amount"]

    def get_total_payment(self, obj):
        return self.get_cart_preview(obj)["total_payment"]
