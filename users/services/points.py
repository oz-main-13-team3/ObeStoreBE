from django.db import IntegrityError, transaction

from users.models import Point, User


class PointError(Exception):
    pass


@transaction.atomic
def apply_point_delta(user: User, delta: int, *, event_key: str | None) -> Point:
    user_locked = User.objects.select_for_update().get(pk=user.pk)

    new_amount = user_locked.point_balance + delta
    if new_amount < 0:
        raise PointError("포인트 작액이 부족합니다.")

    try:
        point = Point.objects.create(
            user=user_locked,
            balance=delta,
            amount=new_amount,
            event_key=event_key,
        )
    except IntegrityError:
        if event_key:
            point = Point.objects.get(event_key=event_key)
            return point
        raise

    user_locked.point_balance = new_amount
    user_locked.save(update_fields=["point_balance"])

    return point


def get_point_balance(user):
    return user.point_balance
