from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
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
        responses=OrderSerializer,
        tags=["orders"],
    ),
    create=extend_schema(
        summary="주문 생성",
        description="장바구니 기반으로 주문을 생성합니다.",
        request=inline_serializer(
            name="OrderCreateRequest",
            fields={
                "address": serializers.IntegerField(help_text="배송지 ID"),
                "used_point": serializers.IntegerField(
                    required=False,
                    default=0,
                    help_text="사용할 포인트 (미입력이면 0)"
                ),
                "delivery_request": serializers.CharField(
                    required=False,
                    allow_blank=True,
                    help_text="배송 시 요청사항"
                ),
                "cart_item_ids": serializers.ListField(
                    child=serializers.IntegerField(),
                    required=False,
                    help_text="주문에 포함할 CartItem ID"
                )
            },
        ),
        responses={
            201: inline_serializer(
                name="OrderCreateResponse",
                fields={
                    "order_id": serializers.IntegerField(),
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
        request=inline_serializer(
            name="OrderCancelPatch",
            fields={"order_status": serializers.ChoiceField(choices=["주문 취소"])},
        ),
        responses=OrderSerializer,
        tags=["orders"],
    ),
    destroy=extend_schema(exclude=True),
)

OrderPreviewSchema = extend_schema(
    summary="주문 결제/적립 미리보기",
    description="상품 금액, 할인 금액, 배송비, 총 결제 금액, 적립 예정 포인트 등을 미리 계산합니다.",
    request=inline_serializer(
        name="OrderPreviewRequest",
        fields={
            "used_point": serializers.IntegerField(required=False, default=0),
            "cart_item_ids": serializers.ListField(
                child=serializers.IntegerField(),
                required=False,
                help_text="주문에 포함할 CartItem ID 목록(없으면 장바구니 전체)"
            )
        }
    ),
    responses=inline_serializer(
        name="OrderPreviewResponse",
        fields={
            "subtotal": serializers.IntegerField(
                help_text="할인 적용 후 상품 총액"
            ),
            "product_discount_amount": serializers.IntegerField(
                help_text="상품 할인 총액(정가 - 할인가 합계)"
            ),
            "discount_amount": serializers.IntegerField(
                help_text="전체 할인 금액(현재는 상품 할인과 동일)"
            ),
            "used_point": serializers.IntegerField(
                help_text="사용 포인트"
            ),
            "delivery_amount": serializers.IntegerField(
                help_text="배송비 (기본 3,500원, 5만 원 이상 무료)"
            ),
            "total_payment": serializers.IntegerField(
                help_text="최종 결제 금액 (상품금액 - 사용포인트 + 배송비)"
            ),
            "expected_point": serializers.IntegerField(
                help_text="이번 주문으로 적립 예정인 포인트 (배송비 제외 금액 기준 1%)"
            ),
            "available_point": serializers.IntegerField(
                help_text="현재 보유 포인트"
            ),
        },
    ),
    tags=["orders"],
)