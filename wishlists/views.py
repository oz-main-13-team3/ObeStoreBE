# wishlist/views.py
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from products.models import Product

from .models import Wishlist
from .schema import wishlists_schema
from .serializers import WishlistSerializer


class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # GET /users/me/wishlist
    @wishlists_schema["list"]
    def list(self, request):
        queryset = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(queryset, many=True, context={"request": request})
        return serializer.data

    # POST /users/me/wishlist
    @wishlists_schema["create"]
    def create(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response(
                {"type": "Bad Request", "detail": "product_id 없음"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"type": "Not Found", "detail": "존재하지 않는 상품"},
                status=status.HTTP_404_NOT_FOUND,
            )

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product_id=product_id
        )

        if not created:
            return Response(
                {"type": "Conflict", "detail": "이미 찜 목록에 있음"},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"CreateSuccess": True},
            status=status.HTTP_201_CREATED,
        )

    # DELETE /users/me/wishlist/<id>/
    @wishlists_schema["destroy"]
    def destroy(self, request, pk=None):
        try:
            wishlist_item = Wishlist.objects.get(pk=pk, user=request.user)
            wishlist_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response(
                {"type": "Not Found", "detail": "존재하지 않는 wishlistItemId"}, status=status.HTTP_404_NOT_FOUND
            )
