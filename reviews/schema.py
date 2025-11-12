from drf_spectacular.utils import OpenApiResponse, extend_schema

from reviews.serializers import ReviewSerializer

reviews_schema = {
    "create": extend_schema(
        summary="상품 리뷰 생성", description="상품 리뷰를 생성합니다.", responses=OpenApiResponse(ReviewSerializer)
    ),
    "list": extend_schema(
        summary="상품 리뷰 조회", description="상품 리뷰를 조회합니다.", responses=OpenApiResponse(ReviewSerializer)
    ),
    "retrieve": extend_schema(
        summary="상품 리뷰 상세 조회",
        description="상품 리뷰를 상세 조회합니다.",
        responses=OpenApiResponse(ReviewSerializer),
    ),
    "update": extend_schema(
        summary="상품 리뷰 수정", description="상품 리뷰를 수정합니다.", responses=OpenApiResponse(ReviewSerializer)
    ),
    "partial_update": extend_schema(
        summary="상품 리뷰 수정", description="상품 리뷰를 수정합니다.", responses=OpenApiResponse(ReviewSerializer)
    ),
    "destroy": extend_schema(
        summary="상품 리뷰 삭제", description="상품 리뷰를 삭제합니다.", responses=OpenApiResponse(ReviewSerializer)
    ),
}
