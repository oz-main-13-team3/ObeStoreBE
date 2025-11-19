# wishlist/serializers.py
from rest_framework import serializers

from products.serializers import ProductListSerializer

from .models import Wishlist


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product"]
