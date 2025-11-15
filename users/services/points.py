from django.db import transaction

from users.models import Point, User


class PointError(Exception):
    pass


@transaction.atomic
def apply_point_delta(user: User, delta: int, *, event_key: str | None) -> Point:
    user_locked = User.objects.select_for_update().get(pk=user.pk)

    new_balance = user_locked.point_balance + delta
    if new_balance < 0:
        raise PointError("포인트 잔액이 부족합니다.")

    if event_key:
        point, created = Point.objects.get_or_create(
            user = user_locked,
            event_key = event_key,
            defaults={
                "amount": delta,
                "balance": new_balance,
            }
        )
        if not created:
            return point
    else:
        point = Point.objects.create(
            user=user_locked,
            amount=delta,
            balance=new_balance,
            event_key=None,
        )

    user_locked.point_balance = new_balance
    user_locked.save(update_fields=["point_balance"])

    return point


def get_point_balance(user):
    return user.point_balance
