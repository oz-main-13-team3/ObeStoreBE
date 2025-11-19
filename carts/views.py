from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    queryset = Cart.objects.all()

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(parameters=[OpenApiParameter("pk", OpenApiTypes.INT, location="path")])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[OpenApiParameter("pk", OpenApiTypes.INT, location="path")])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(parameters=[OpenApiParameter("pk", OpenApiTypes.INT, location="path")])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    queryset = CartItem.objects.all()

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="product_id",
                type=OpenApiTypes.INT,
                location="query",
                description="특정 상품 ID로 필터링",
                required=False,
            )
        ]
    )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product = serializer.validated_data["product"]
        if not product:
            raise ValidationError({"product": "This field is required."})

        cart_items = CartItem.objects.filter(cart=cart, product=product)
        if cart_items.exists():
            cart_item = cart_items.first()
            cart_item.amount += serializer.validated_data.get("amount", 1)
            cart_item.save()
        else:
            serializer.save(cart=cart)

    @extend_schema(parameters=[OpenApiParameter("pk", OpenApiTypes.INT, location="path")])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(parameters=[OpenApiParameter("pk", OpenApiTypes.INT, location="path")])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
