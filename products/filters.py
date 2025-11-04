from django_filters import rest_framework as filters

from products.models import Product


class ProductFilter(filters.FilterSet):
    category_name = filters.CharFilter(field_name="category__category_name", lookup_expr="iexact")
    min_rating = filters.NumberFilter(field_name="product_rating", lookup_expr="gte")
    has_review = filters.BooleanFilter(method="filter_has_review")

    class Meta:
        model = Product
        fields = ["category_name", "min_rating", "has_review"]

    def filter_has_review(self, queryset, name, value):
        from django.db.models import Count

        queryset = queryset.annotate(review_count=Count("review"))
        if value:
            return queryset.filter(review_count__gt=0)
        else:
            return queryset.filter(review_count=0)
