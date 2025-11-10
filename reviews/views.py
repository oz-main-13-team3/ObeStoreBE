from django_filters.rest_framework import DjangoFilterBackend
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
