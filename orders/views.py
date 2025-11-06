# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from carts.models import CartItem
from orders.models import Order
from users.models import Point


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Create_order(request):
    user = request.user
    used_point = int(request.POST.get("used_point", 0))
    cart_item = CartItem.objects.filter(user=user, is_active=True)

    total = sum(item.product.product_value * item.amount for item in cart_item)
    if used_point > user.services.points:
        return Response({"error": "포인트 부족"}, status=400)

    pay_amount = total - used_point

    order = Order.objects.create(user=user, used_point=used_point, order_status="결제대기")

    return Response({"orderId": str(order.order_number), "amount": pay_amount, "orderName": "장바구니 결제"})


def confirm_payment(request):
    payment_key = request.data.get("paymentKey")
    order_id = request.data.get("orderId")
    user = request.user

    order = Order.objects.get(order_number=order_id, user=user)
    order.payment_key = payment_key
    order.order_status = "결제완료"
    order.save()

    total_amount = sum(item.product.product_value * item.amount for item in order.order_products.all())

    # 최신 포인트
    last_point = Point.objects.filter(user=user).order_by("-updated_at").first()
    if last_point:
        current_balance = last_point.balance
    else:
        current_balance = 0

    new_balance = current_balance - order.used_point
    earned_point = int(total_amount * 0.01)
    new_balance += earned_point

    Point.objects.create(
        user=user,
        amount=earned_point,
        balance=new_balance,
    )

    return Response({"message": "결제 완료 및 포인트 적립 성공", "balance": new_balance})
