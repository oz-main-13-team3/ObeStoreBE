from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny

from products.filters import ProductFilter
from products.models import Product, ProductQna
from products.permissions import IsOwnerOrAdmin
from products.serializer import ProductQnaCreateSerializer, ProductQnaSerializer, ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["product_name"]
    ordering_fields = ["sales", "product_value", "created_at", "review_count"]
    ordering = ["-created_at"]  # 기본 정렬
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "tag", "brand").all()
        ordering_param = self.request.query_params.get("ordering", "")

        if "review_count" in ordering_param:
            from django.db.models import Count

            queryset = queryset.annotate(review_count=Count("review"))
        return queryset


class ProductQnaViewSet(viewsets.ModelViewSet):
    queryset = ProductQna.objects.all()
    serializer_class = ProductQnaSerializer  # 기본값 (조회용)
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return ProductQnaCreateSerializer
        return ProductQnaSerializer

    def get_queryset(self):
        # Nested URL에서 product_pk를 가져와서 필터링
        product_id = self.kwargs.get("product_pk")
        if product_id:
            return ProductQna.objects.filter(product_id=product_id)
        return ProductQna.objects.all()
