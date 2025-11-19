from drf_spectacular.utils import OpenApiResponse, extend_schema

from wishlists.serializers import WishlistSerializer

wishlists_schema = {
    "create": extend_schema(
        summary="상품 리뷰 생성", description="상품 리뷰를 생성합니다.", responses=OpenApiResponse(WishlistSerializer)
    ),
    "list": extend_schema(
        summary="상품 리뷰 조회", description="상품 리뷰를 조회합니다.", responses=OpenApiResponse(WishlistSerializer)
    ),
    "destroy": extend_schema(
        summary="상품 리뷰 삭제", description="상품 리뷰를 삭제합니다.", responses=OpenApiResponse(WishlistSerializer)
    ),
}