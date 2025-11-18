from decimal import Decimal
from typing import Iterable, Optional

from django.db import transaction
from rest_framework.exceptions import ValidationError

from carts.models import CartItem
from orders.models import Order, OrderProduct
from products.models import Product
from users.models import Address
from users.services.points import get_point_balance


class OrderService:
    @staticmethod
    def _get_cart_items(user, cart_item_ids: Optional[Iterable[int]] = None):
        qs = CartItem.objects.filter(cart__user=user)
        if cart_item_ids:
            qs = qs.filter(id__in=cart_item_ids)
        if not qs.exists():
            raise ValidationError({"cart": "선택된 장바구니가 비어 있습니다."})
        return qs

    @staticmethod
    def compute_delivery_amount(subtotal: int) -> int:
        FREE_THRESHOLD = 50000
        BASE_DELIVERY_FEE = 3500

        if subtotal >= FREE_THRESHOLD:
            return 0
        return BASE_DELIVERY_FEE

    @staticmethod
    def compute_expected_point(base: int) -> int:
        return int(base * 0.01)

    @staticmethod
    def preview_order(user, data):
        cart_item_ids = data.get("cart_item_ids") or []
        if cart_item_ids and not isinstance(cart_item_ids, (list, tuple)):
            raise ValidationError({"cart_item_ids": "리스트 형태여야 합니다."})

        cart_items = OrderService._get_cart_items(user, cart_item_ids)

        used_point = int(data.get("used_point") or 0)

        user_point = get_point_balance(user)
        if used_point > user_point:
            raise ValidationError({"used_point": f"보유 포인트({user_point})보다 많이 사용할 수 없습니다."})
        MIN_POINT_BALANCE = 5000
        if used_point > 0 and user_point < MIN_POINT_BALANCE:
            raise ValidationError({"used_point": f"보유 포인트가 {MIN_POINT_BALANCE}P 이상일 떄만 사용 가능합니다."})

        subtotal = 0
        product_discount_total = 0

        for item in cart_items:
            p = item.product
            if not p:
                continue

            original_price = p.product_value
            rate = p.discount_rate or Decimal("0")
            discounted_price = int(
                Decimal(original_price) * (Decimal("1") - rate)
            )
            item_discount_total = (original_price - discounted_price) * item.amount
            product_discount_total += item_discount_total
            subtotal += discounted_price * item.amount

        discount_amount = product_discount_total
        delivery_amount = OrderService.compute_delivery_amount(subtotal)
        total_payment = subtotal - used_point + delivery_amount
        if total_payment < 0:
            raise ValidationError({"total_payment": "결제 금액이 0보다 작을 수 없습니다."})

        expected_base = total_payment - delivery_amount
        if expected_base < 0:
            expected_base = 0
        expected_point = OrderService.compute_expected_point(expected_base)

        return {
            "subtotal": subtotal,   # 상품 금액
            "product_discount_amount": product_discount_total,  # 상품 할인 총액
            "discount_amount": discount_amount,  # 전체 할인 금액
            "used_point": used_point,   # 적립 사용 금액
            "delivery_amount": delivery_amount, # 배송비
            "total_payment": total_payment,     # 총 결제 금액
            "expected_point": expected_point,   # 적립 예정 포인트
            "available_point": user_point,  # 현재 보유 포인트
        }

    @staticmethod
    @transaction.atomic
    def create_order(user, data):
        address_id = data.get("address")

        if address_id:
            address = Address.objects.filter(id=address_id, user=user).first()
            if not address:
                raise ValidationError({"address": "본인 배송지만 사용할 수 있습니다."})
        else:
            address = Address.objects.filter(user=user, is_default=True).first()
            if not address:
                raise ValidationError({"address": "배송지 ID를 전달하지 않았고, 기본 배송지도 없습니다."})

        cart_item_ids = data.get("cart_item_ids") or []
        if cart_item_ids and not isinstance(cart_item_ids, (list, tuple)):
            raise ValidationError({"cart_item_ids": "리스트 형태여야 합니다."})

        cart_items = OrderService._get_cart_items(user, cart_item_ids)

        used_point = int(data.get("used_point") or 0)
        user_point = get_point_balance(user)
        if used_point > user_point:
            raise ValidationError({"used_point": f"보유 포인트({user_point})보다 많이 사용할 수 없습니다."})
        MIN_POINT_BALANCE = 5000
        if used_point > 0 and user_point < MIN_POINT_BALANCE:
            raise ValidationError({"used_point": f"보유 포인트가 {MIN_POINT_BALANCE}P 이상일 떄만 사용 가능합니다."})

        product_ids = [i.product_id for i in cart_items]
        products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

        subtotal = 0
        product_discount_total = 0

        for item in cart_items:
            p = products.get(item.product_id)
            if not p:
                raise ValidationError({"product": f"상품(id={item.product_id}) 정보를 찾을 수 없습니다."})
            if getattr(p, "product_stock", 0) < item.amount:
                raise ValidationError({"stock": f"'{p.product_stock}' 재고 부족 (요청: {item.amount})"})

            original_price = p.product_value
            rate = p.discount_rate or Decimal("0")
            discounted_price = int(Decimal(original_price) * (Decimal("1") - rate))
            item_discount_total = (original_price - discounted_price) * item.amount
            product_discount_total += item_discount_total
            subtotal += discounted_price * item.amount

        discount_amount = product_discount_total
        delivery_amount = OrderService.compute_delivery_amount(subtotal)
        delivery_request = data.get("delivery_request")

        total_payment = subtotal - used_point + delivery_amount
        if total_payment < 0:
            raise ValidationError({"total_payment": "결제 금액이 0보다 작을 수 없습니다."})

        order = Order.objects.create(
            user=user,
            address=address,
            subtotal=subtotal,
            discount_amount=discount_amount,
            delivery_amount=delivery_amount,
            total_payment=total_payment,
            used_point=used_point,
            order_status="접수 완료",
            delivery_request=delivery_request,
        )

        order_products = []
        for item in cart_items:
            p = item.product
            rate = p.discount_rate or Decimal("0")
            discounted_price = int(Decimal(p.product_value) * (Decimal("1") - rate))
            order_products.append(
                OrderProduct(
                    order=order,
                    product=p,
                    amount=item.amount,
                    price=discounted_price,
                    total_price=discounted_price * item.amount,
                )
            )

        OrderProduct.objects.bulk_create(order_products)
        return order
