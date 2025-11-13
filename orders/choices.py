from django.db.models import TextChoices


class OrderStatus(TextChoices):
    RECEIVED = "접수 완료", "접수 완료"
    FAILED = "주문 실패", "주문 실패"
    COMPLETED = "주문 완료", "주문 완료"


class DeliveryStatus(TextChoices):
    PREPARING = "배송 준비", "배송 준비"
    SHIPPING = "배송 중", "배송 중"
    DELIVERED = "배송 완료", "배송 완료"


class PaymentStatus(TextChoices):
    READY = "ready", "ready"
    SUCCESS = "success", "success"
    FAILED = "failed", "failed"


class PaymentMethod(TextChoices):
    TOSS_PAY = "tosspay", "tosspay"
