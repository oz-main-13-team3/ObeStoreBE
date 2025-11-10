from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderProduct, Payment


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    fields = ("product", "amount", "price", "total_price", "created_at")
    readonly_fields = ("price", "total_price", "created_at")


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    fields = (
        "payment_status",
        "payment_method",
        "payment_amount",
        "toss_order_id",
        "toss_payment_key",
        "receipt_link",
        "approved_at",
        "fail_code",
        "fail_message",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "payment_status",
        "payment_method",
        "payment_amount",
        "toss_order_id",
        "toss_payment_key",
        "receipt_link",
        "approved_at",
        "fail_code",
        "fail_message",
        "created_at",
        "updated_at",
    )

    @admin.display(description="영수증")
    def receipt_link(self, obj: Payment):
        if obj.receipt_url:
            return format_html('<a href="{}" target="_blank">열기</a>', obj.receipt_url)
        return "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_order_number",
        "user",
        "address",
        "order_status",
        "delivery_status",
        "subtotal",
        "discount_amount",
        "delivery_amount",
        "used_point",
        "total_payment",
        "payments_count",
        "created_at",
    )
    list_filter = ("order_status", "delivery_status", "created_at")
    search_fields = ("order_number", "user__email", "user__username", "address__name")
    ordering = ("-created_at",)
    readonly_fields = (
        "order_number",
        "subtotal",
        "discount_amount",
        "delivery_amount",
        "used_point",
        "total_payment",
        "created_at",
        "updated_at",
    )
    inlines = [OrderProductInline, PaymentInline]
    list_per_page = 30

    @admin.display(description="주문번호")
    def short_order_number(self, obj: Order):
        return str(obj.order_number).split("-")[0]

    @admin.display(description="결제건수")
    def payments_count(self, obj: Order):
        return obj.payments.count()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "payment_status",
        "payment_method",
        "payment_amount",
        "toss_order_id",
        "approved_at",
        "receipt_link",
        "created_at",
    )
    list_filter = ("payment_status", "payment_method", "approved_at", "created_at")
    search_fields = ("toss_order_id", "toss_payment_key", "order__order_number", "order__user__email")
    readonly_fields = (
        "order",
        "payment_status",
        "payment_method",
        "payment_amount",
        "toss_order_id",
        "toss_payment_key",
        "receipt_link",
        "approved_at",
        "fail_code",
        "fail_message",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    @admin.display(description="영수증")
    def receipt_link(self, obj: Payment):
        if obj.receipt_url:
            return format_html('<a href="{}" target="_blank">열기</a>', obj.receipt_url)
        return "-"


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "amount", "price", "total_price", "created_at")
    list_filter = ("created_at",)
    search_fields = ("order__order_number", "product__product_name")
    readonly_fields = ("price", "total_price", "created_at", "updated_at")
    ordering = ("-created_at",)
