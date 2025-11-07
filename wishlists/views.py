# wishlist/views.py
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from products.models import Product

from .models import Wishlist
from .serializers import WishlistSerializer


class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # GET /users/me/wishlist
    def list(self, request):
        queryset = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(queryset, many=True)
        return Response({"Success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    # POST /users/me/wishlist
    def create(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"type": "Bad Request", "detail": "product_id 없음"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wishlist, created = Wishlist.objects.get_or_create(user=request.user, product_id=product_id)
            if not created:
                return Response({"type": "Conflict", "detail": "이미 찜 목록에 있음"}, status=status.HTTP_409_CONFLICT)
            return Response({"CreateSuccess": True}, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({"type": "Not Found", "detail": "존재하지 않는 상품"}, status=status.HTTP_404_NOT_FOUND)

    # DELETE /users/me/wishlist/<id>/
    def destroy(self, request, pk=None):
        try:
            wishlist_item = Wishlist.objects.get(id=pk, user=request.user)
            wishlist_item.delete()
            return Response({"Success": True}, status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response(
                {"type": "Not Found", "detail": "존재하지 않는 wishlistItemId"}, status=status.HTTP_404_NOT_FOUND
            )
