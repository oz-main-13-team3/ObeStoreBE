from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from orders.serializers import PaymentSerializer, ReadyPaymentResponseSerializer

PaymentSchema = extend_schema_view(
    list=extend_schema(
        summary="결제 목록(관리자)",
        description="관리자만 결제 목록을 조회합니다.",
        responses=PaymentSerializer(many=True),
        tags=["payments"],
    ),
    retrieve=extend_schema(
        summary="결제 단건 조회",
        description="관리자 또는 소유자만 단건 결제를 조회합니다.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, "path")],
        responses=PaymentSerializer,
        tags=["payments"],
    ),
    create=extend_schema(
        summary="결제 준비",
        description="Toss 결제 페이지로 이동하기 전 필요한 값을 생성/반환합니다.",
        request=inline_serializer(
            name="ReadyPaymentRequest",
            fields={
                "order_id": serializers.IntegerField(),
            },
        ),
        responses=ReadyPaymentResponseSerializer,
        tags=["payments"],
    ),
)

TossSuccessSchema = extend_schema(
    summary="Toss 결제 성공 브리지",
    description="Toss 결제 완료 후 PG/프론트에서 백엔드로 리다이렉트될 때 confirm(승인)을 수행합니다.",
    tags=["payments"],
    parameters=[
        OpenApiParameter(name="paymentKey", type=OpenApiTypes.STR, location="query", required=True),
        OpenApiParameter(name="orderId", type=OpenApiTypes.STR, location="query", required=True),
        OpenApiParameter(name="amount", type=OpenApiTypes.INT, location="query", required=True),
    ],
    responses=inline_serializer(
        name="TossSuccessResponse",
        fields={
            "status": serializers.CharField(),  # "success"
            "order_number": serializers.CharField(),  # 내부 주문번호(표시용)
            "receipt_url": serializers.CharField(allow_null=True, required=False),
        },
    ),
)

TossFailSchema = extend_schema(
    summary="Toss 결제 실패 브리지",
    description="Toss 결제 실패/취소 시 실패 정보를 백엔드로 전달합니다.",
    tags=["payments"],
    parameters=[
        OpenApiParameter(name="code", type=OpenApiTypes.STR, location="query", required=False),
        OpenApiParameter(name="message", type=OpenApiTypes.STR, location="query", required=False),
        OpenApiParameter(name="orderId", type=OpenApiTypes.STR, location="query", required=False),
    ],
    responses=inline_serializer(
        name="TossFailResponse",
        fields={
            "status": serializers.CharField(),  # "fail"
            "code": serializers.CharField(allow_null=True, required=False),
            "message": serializers.CharField(allow_null=True, required=False),
            "orderId": serializers.CharField(allow_null=True, required=False),
        },
    ),
)
