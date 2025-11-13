from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from orders.serializers import OrderSerializer

OrderSchema = extend_schema_view(
    list=extend_schema(
        summary="주문 목록",
        description="로그인한 사용자의 주문 목록을 조회합니다.",
        responses=OrderSerializer(many=True),
        tags=["orders"],
    ),
    retrieve=extend_schema(
        summary="주문 단건 조회",
        description="로그인한 사용자의 주문 상세를 조회합니다.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, "path")],
        responses=OrderSerializer,
        tags=["orders"],
    ),
    create=extend_schema(
        summary="주문 생성",
        description="장바구니 기반으로 주문을 생성합니다.",
        request=OrderSerializer,
        responses={
            201: inline_serializer(
                name="OrderCreateResponse",
                fields={
                    "order_number": serializers.CharField(),
                    "message": serializers.CharField(),
                    "pay_amount": serializers.IntegerField(),
                },
            )
        },
        tags=["orders"],
    ),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(
        summary="주문 취소(PATCH 전용)",
        description="주문 상태를 '주문 취소'로 변경만 허용합니다. 결제 완료 주문은 취소 불가.",
        parameters=[OpenApiParameter("pk", OpenApiTypes.INT, "path")],
        request=inline_serializer(
            name="OrderCancelPatch",
            fields={"order_status": serializers.ChoiceField(choices=["주문 취소"])},
        ),
        responses=OrderSerializer,
        tags=["orders"],
    ),
    destroy=extend_schema(exclude=True),
)
