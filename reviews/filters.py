from django_filters import rest_framework as filters

from reviews.models import Review


class ReviewFilter(filters.FilterSet):
    product_name = filters.CharFilter(field_name="product__product_name", lookup_expr="icontains")

    class Meta:
        model = Review
        fields = ["product_name"]
