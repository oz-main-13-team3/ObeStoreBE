from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from products.filters import ProductFilter
from products.models import Product, ProductQna
from products.serializers import ProductListSerializer, ProductQnaCreateSerializer, ProductQnaSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["product_name"]
    ordering_fields = ["sales", "product_value", "created_at", "review_count"]
    ordering = ["-created_at"]
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "tag", "brand").all()
        ordering_param = self.request.query_params.get("ordering", "")

        if "review_count" in ordering_param:
            from django.db.models import Count

            queryset = queryset.annotate(review_count=Count("review"))
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            from products.serializers import ProductDetailSerializer

            return ProductDetailSerializer
        else:
            from products.serializers import ProductListSerializer

            return ProductListSerializer

    @extend_schema(
        summary="상품 리스트 조회",
        description="상품 목록을 조회합니다. 검색/정렬/필터링 가능",
        responses=OpenApiResponse(ProductListSerializer),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="상품 상세 조회",
        description="상품 상세 정보를 조회합니다.",
        responses=OpenApiResponse(ProductListSerializer),
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class ProductQnaViewSet(viewsets.ModelViewSet):
    queryset = ProductQna.objects.all()
    serializer_class = ProductQnaSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ProductQnaCreateSerializer
        return ProductQnaSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update"]:
            permission_classes = [IsAdminUser]
        elif self.action == "create":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="상품 모든 문의 조회",
        description="상품 문의를 조회합니다.",
        responses=OpenApiResponse(ProductQnaSerializer),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="상품의 특정 문의 조회",
        description="상품의 특정 문의를 조회합니다.",
        responses=OpenApiResponse(ProductQnaSerializer),
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="상품 문의 수정",
        description="상품 문의를 수정합니다.",
        responses=OpenApiResponse(ProductQnaSerializer),
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="상품 문의 수정",
        description="상품 문의를 수정합니다.",
        responses=OpenApiResponse(ProductQnaSerializer),
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="상품 문의 삭제",
        description="상품 문의를 삭제합니다.",
        responses=OpenApiResponse(ProductQnaSerializer),
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="상품 문의 생성",
        description="상품 문의를 생성합니다.",
        responses=OpenApiResponse(ProductQnaCreateSerializer),
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        return ProductQna.objects.all()


@extend_schema_view(
    get=extend_schema(
        summary="특정 상품 모든 문의 조회",
        description="특정 상품의 모든 문의를 조회합니다.",
        responses=OpenApiResponse(ProductQnaSerializer),
    )
)
class ProductQnaListView(ListAPIView):
    serializer_class = ProductQnaSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_pk")
        return ProductQna.objects.filter(product_id=product_id)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
