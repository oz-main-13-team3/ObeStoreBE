from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.services.points import PointError, apply_point_delta

from .models import Review


def _earn_rate() -> Decimal:
    return Decimal(str(getattr(settings, "REVIEW_REWARD_RATE", 0.10)))


def _round_mode():
    mode = str(getattr(settings, "REVIEW_REWARD_ROUND", "floor")).lower()
    if mode == "ceil":
        return ROUND_CEILING
    if mode == "round":
        return ROUND_HALF_UP
    return ROUND_FLOOR


def _reward_min() -> int | None:
    v = getattr(settings, "REVIEW_REWARD_MIN", None)
    return int(v) if v is not None else None


def _reward_max() -> int | None:
    v = getattr(settings, "REVIEW_REWARD_MAX", None)
    return int(v) if v is not None else None


def _price_attr_name() -> str:
    return getattr(settings, "REVIEW_REWARD_PRICE_ATTR", "product_value")


def _get_product_price(review: "Review") -> int:
    product = getattr(review, "product", None)
    if not product:
        return 0
    attr = _price_attr_name()
    price = getattr(product, attr, None)
    if price is None:
        return 0
    try:
        return int(Decimal(str(price)))
    except (ValueError, TypeError, InvalidOperation):  # 에러가 광범위하다고 되어있어서 넣었습니다.
        return 0


def _compute_review_reward(review: "Review") -> int:
    price = _get_product_price(review)
    if price <= 0:
        return 0

    rate = _earn_rate()
    mode = _round_mode()

    raw = (Decimal(price) * rate).quantize(Decimal("1"), rounding=mode)
    reward = int(raw)

    mn = _reward_min()
    mx = _reward_max()
    if mn is not None:
        reward = max(reward, mn)
    if mx is not None:
        reward = min(reward, mx)

    return max(reward, 0)


@receiver(post_save, sender=Review)
def award_points_for_review(sender, instance: "Review", created: bool, **kwargs):
    if not created:
        return

    user = getattr(instance, "user", None)
    product_id = getattr(instance, "product_id", None)
    if not user or not product_id:
        return  # 안전장치

    reward = _compute_review_reward(instance)
    if reward <= 0:
        return

    event_key = f"review:{user.id}:{product_id}:earn"

    def _apply():
        try:
            apply_point_delta(user, reward, event_key=event_key)
        except PointError:
            pass
        except (ValueError, TypeError):
            pass

    transaction.on_commit(_apply)
