# wishlist/serializers.py
from rest_framework import serializers
from .models import Wishlist

class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_value = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    brand_id = serializers.IntegerField(source='product.brand.id', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_name', 'product_value', 'brand_id']
