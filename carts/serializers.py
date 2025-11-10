from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.product_name")
    price = serializers.ReadOnlyField(source="product.product_value")
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = "__all__"

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

    def get_total_price(self, obj):
        total = 0
        for item in obj.items.all():
            if item.product:
                total += item.product.product_value * item.amount
        return total
