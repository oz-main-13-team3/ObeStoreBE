from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver

from carts.services import clear_user_cart
from orders.models import Order
from users.services.points import PointError, apply_point_delta


def _status_changed_to_completed(instance: Order) -> bool:
    if not instance.pk:
        return False
    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return False
    return old.order_status != "주문 완료" and instance.order_status == "주문 완료"


def _round_mode():
    m = str(getattr(settings, "ORDER_POINT_ROUND", "floor")).lower()
    if m == "ceil":
        return ROUND_CEILING
    if m == "round":
        return ROUND_HALF_UP
    return ROUND_FLOOR


def _as_decimal(v, default="0.01") -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v if v is not None else default))


def _compute_order_reward(order: Order) -> int:
    amount = int(order.total_payment or 0)
    if amount <= 0:
        return 0

    rate = _as_decimal(getattr(settings, "ORDER_POINT_EARN_RATE", Decimal("0.01")))
    raw = (Decimal(amount) * rate).quantize(Decimal("1"), rounding=_round_mode())
    reward = int(raw)

    mn = getattr(settings, "ORDER_POINT_MIN", None)
    mx = getattr(settings, "ORDER_POINT_MAX", None)
    if mn is not None:
        reward = max(reward, int(mn))
    if mx is not None:
        reward = min(reward, int(mx))
    return max(reward, 0)


@receiver(pre_save, sender=Order)
def _on_order_completed(sender, instance: Order, **kwargs):
    if not _status_changed_to_completed(instance):
        return

    user = getattr(instance, "user", None)
    if not user:
        return

    used_point = int(getattr(instance, "used_point", 0) or 0)
    point_event_key = f"order:{instance.pk}:use_point"
    earn_event_key = f"order:{instance.pk}:earn_point"

    def _after_commit():
        try:
            clear_user_cart(user)
        except Exception:
            pass

        if used_point > 0:
            try:
                apply_point_delta(user, -used_point, event_key=point_event_key)
            except PointError:
                pass
            except Exception:
                pass

        try:
            reward = _compute_order_reward(instance)
            if reward > 0:
                apply_point_delta(user, reward, event_key=earn_event_key)
        except PointError:
            pass
        except Exception:
            pass

    transaction.on_commit(_after_commit)
