from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from reviews.filters import ReviewFilter
from reviews.models import Keyword, Review, ReviewImage, ReviewKeyword
from reviews.serializers import (
    KeywordSerializer,
    ReviewImageSerializer,
    ReviewKeywordSerializer,
    ReviewSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReviewFilter

    ordering_fields = ["rating", "created_at", "product_review_count"]
    ordering = ["-created_at"]  # 기본 정렬: 최신 등록순

    def get_queryset(self):
        from django.db.models import Count

        return Review.objects.annotate(product_review_count=Count("product__product_reviews"))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="상품 리뷰 생성",
        description="상품 리뷰를 생성합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="상품 리뷰 조회",
        description="상품 리뷰를 조회합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="상품 리뷰 상세 조회",
        description="상품 리뷰를 상세 조회합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="상품 리뷰 수정",
        description="상품 리뷰를 수정합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="상품 리뷰 수정",
        description="상품 리뷰를 수정합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="상품 리뷰 삭제",
        description="상품 리뷰를 삭제합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ReviewKeywordViewSet(viewsets.ModelViewSet):
    queryset = ReviewKeyword.objects.all()
    serializer_class = ReviewKeywordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        review_id = request.query_params.get("review_id")
        queryset = self.get_queryset()
        if review_id:
            queryset = queryset.filter(review_id=review_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class KeywordViewSet(viewsets.ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewImageViewSet(viewsets.ModelViewSet):
    queryset = ReviewImage.objects.all()
    serializer_class = ReviewImageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
