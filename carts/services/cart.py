from carts.models import CartItem


def clear_user_cart(user) -> int:
    if not user:
        return 0
    deleted_count, _ = CartItem.objects.filter(cart__user=user).delete()
    return deleted_count
