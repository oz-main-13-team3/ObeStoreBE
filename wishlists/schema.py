from drf_spectacular.utils import OpenApiResponse, extend_schema

from wishlists.serializers import WishlistSerializer

wishlists_schema = {
    "create": extend_schema(
        summary="찜 목록 추가", description="상품을 찜 목록에 추가합니다.", responses=OpenApiResponse(WishlistSerializer)
    ),
    "list": extend_schema(
        summary="찜 목록 조회", description="찜 목록을 조회합니다.", responses=OpenApiResponse(WishlistSerializer)
    ),
    "destroy": extend_schema(
        summary="찜 목록 삭제", description="찜 목록을 삭제합니다.", responses=OpenApiResponse(WishlistSerializer)
    ),
}