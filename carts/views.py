from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

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


class CartItemViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    queryset = Cart.objects.all()

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
    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product = serializer.validated_data["product"]
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
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
