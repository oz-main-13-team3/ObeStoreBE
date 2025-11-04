from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from products.filters import ProductFilter
from products.models import Product
from products.serializer import ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["product_name"]
    ordering_fields = ["sales", "product_value", "created_at", "review_count"]
    ordering = ["-created_at"]  # 기본 정렬

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "tag", "brand").all()
        ordering_param = self.request.query_params.get("ordering", "")

        if "review_count" in ordering_param:
            from django.db.models import Count

            queryset = queryset.annotate(review_count=Count("review"))
        return queryset
