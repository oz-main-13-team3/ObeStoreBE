from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from carts.models import CartItem
from orders.models import Order, OrderProduct
from orders.serializers import OrderSerializer
from products.models import Product
from users.models import Address, Point
from users.services.points import get_point_balance


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user", "address").prefetch_related("order_products__product")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user

        address_id = request.data.get("address")
        if not address_id:
            raise ValidationError({"address": "배송지 ID를 반드시 전달해야 합니다."})

        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            raise NotFound("해당 배송지를 찾을 수 없습니다.")
        if address.user != user:
            raise ValidationError({"address": "본인 주소만 선택할 수 있습니다."})

        cart_items = CartItem.objects.filter(cart__user=user).select_related("product")
        if not cart_items.exists():
            raise ValidationError({"cart": "장바구니가 비어 있습니다."})

        used_point = int(request.data.get("used_point", 0))
        user_point = get_point_balance(user)
        if used_point > user_point:
            raise ValidationError({"used_point": f"보유 포인트({user_point})보다 많이 사용할 수 없습니다."})

        product_ids = [item.product_id for item in cart_items]
        products_qs = Product.objects.select_for_update().filter(id__in=product_ids)
        products_map = {p.id: p for p in products_qs}

        order_products_payload = []
        subtotal = 0

        for item in cart_items:
            product = products_map.get(item.product_id)
            if not product:
                raise ValidationError({"product": f"상품(id={item.product_id}) 정보를 찾을 수 없습니다."})
            qty = item.amount

            if hasattr(product, "stock") and product.product_stock < qty:
                raise ValidationError(
                    {"stock": f"'{product.product_stock}' 재고 부족 (보유: {product.stock}, 요청: {qty})"}
                )

            price = product.product_value
            total_price = price * qty
            subtotal += total_price

            order_products_payload.append(
                {
                    "product": product.id,
                    "amount": qty,
                }
            )

        discount_amount = int(request.data.get("discount_amount", 0))
        delivery_amount = int(request.data.get("delivery_amount", 0))
        total_payment = subtotal - discount_amount - used_point + delivery_amount
        if total_payment < 0:
            raise ValidationError({"total_payment": "결제 금액이 0보다 작을 수 없습니다."})

        payload = {
            "address": address.id,
            "discount_amount": discount_amount,
            "delivery_amount": delivery_amount,
            "used_point": used_point,
            "order_products": order_products_payload,
        }

        serializer = self.get_serializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        order = serializer.save(user=user, order_status="결제대기")

        for item in order_products_payload:
            product = products_map[item["product"]]
            amount = item["amount"]
            price = product.product_value
            total_price = price * amount

            OrderProduct.objects.create(
                order=order,
                product=product,
                amount=amount,
                price=price,
                total_price=total_price,
            )

        order.subtotal = subtotal
        order.total_payment = total_payment
        order.save()

        if used_point > 0:
            Point.objects.create(user=user, change_amount=-used_point, reason="주문 결제 시 사용")

        return Response(
            {
                "order_number": str(order.order_number),
                "message": "주문이 생성되었습니다. 결제 진행 후 결제가 완료되면 장바구니가 비워집니다.",
                "pay_amount": total_payment,
            },
            status=status.HTTP_201_CREATED,
        )
