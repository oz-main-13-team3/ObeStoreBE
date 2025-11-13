from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from carts.models import CartItem
from orders.models import Order, OrderProduct
from products.models import Product
from users.models import Address
from users.services.points import get_point_balance


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, data):
        address_id = data.get("address")
        if not address_id:
            raise ValidationError({"address": "배송지 ID를 반드시 전달해야 합니다."})

        address = Address.objects.filter(id=address_id).first()
        if not address:
            raise NotFound("해당 배송지를 찾을 수 없습니다.")
        if address.user_id != user.id:
            raise ValidationError({"address": "본인 주소만 선택할 수 있습니다."})

        cart_items = CartItem.objects.filter(cart__user=user).select_related("product")
        if not cart_items.exists():
            raise ValidationError({"cart": "장바구니가 비어 있습니다."})

        used_point = int(data.get("used_point") or 0)
        user_point = get_point_balance(user)
        if used_point > user_point:
            raise ValidationError({"used_point": f"보유 포인트({user_point})보다 많이 사용할 수 없습니다."})

        discount_amount = int(data.get("discount_amount") or 0)
        delivery_amount = int(data.get("delivery_amount") or 0)

        product_ids = [i.product_id for i in cart_items]
        products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

        subtotal = 0
        for item in cart_items:
            p = products.get(item.product_id)
            if not p:
                raise ValidationError({"product": f"상품(id={item.product_id}) 정보를 찾을 수 없습니다."})
            if getattr(p, "product_stock", 0) < item.amount:
                raise ValidationError({"stock": f"'{p.product_stock}' 재고 부족 (요청: {item.amount})"})
            subtotal += p.product_value * item.amount

        total_payment = subtotal - discount_amount - used_point + delivery_amount
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
        )

        OrderProduct.objects.bulk_create(
            [
                OrderProduct(
                    order=order,
                    product=item.product,
                    amount=item.amount,
                    price=item.product.product_value,
                    total_price=item.product.product_value * item.amount,
                )
                for item in cart_items
            ]
        )
        return order
