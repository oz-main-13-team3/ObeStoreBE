from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from orders.models import Order, OrderProduct
from reviews.filters import ReviewFilter
from reviews.models import Keyword, Review, ReviewImage, ReviewKeyword
from reviews.schema import reviews_schema
from reviews.serializers import (
    KeywordSerializer,
    ReviewCreateSerializer,
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
    ordering = ["-created_at"]

    @reviews_schema["list"]
    def list(self, request, *args, **kwargs):
        ordering_parm = request.query_params.get("ordering")

        if ordering_parm == "":
            request.query_params._mutable = True
            del request.query_params["ordering"]
            request.query_params._mutable = False

        if ordering_parm and ordering_parm.lstrip("-") not in self.ordering_fields:
            request.query_params._mutable = True
            del request.query_params["ordering"]
            request.query_params._mutable = False

        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        from django.db.models import Count

        return Review.objects.annotate(product_review_count=Count("product__product_reviews"))

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user

        if not user or user.is_anonymous:
            raise NotAuthenticated("로그인이 필요합니다.")

        product = serializer.validated_data.get("product")

        if product is None:
            raise ValidationError({"product": "상품은 필수입니다."})

        writable, message = self.check_writable(product)

        if not writable:
            raise ValidationError({"detail": message})

        serializer.save(user=user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReviewCreateSerializer
        return ReviewSerializer

    def check_writable(self, product):
        user = self.request.user

        if not user or user.is_anonymous:
            return False, "로그인이 필요합니다."

        if Review.objects.filter(user=user, product=product).exists():
            return False, "이미 해당 상품에 대한 리뷰를 작성했습니다."

        delivered_orders = Order.objects.filter(
            user=user,
            delivery_status="배송 완료"
        )

        purchased = OrderProduct.objects.filter(
            order__in=delivered_orders,
            product=product
        ).exists()

        if not purchased:
            return False, "상품 구매 이력이 없거나 배송이 완료되지 않았습니다."

        return True, "리뷰 작성이 가능합니다."

    @reviews_schema["create"]
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @reviews_schema["retrieve"]
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @reviews_schema["update"]
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @reviews_schema["partial_update"]
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @reviews_schema["destroy"]
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
