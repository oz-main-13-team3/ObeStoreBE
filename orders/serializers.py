from rest_framework import serializers

from users.models import Address

from .models import Order, OrderProduct


class OrderProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderProduct
        fields = ["id", "product", "product_name", "amount", "price", "total_price"]
        read_only_fields = ["price", "total_price"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    order_products = OrderProductSerializer(many=True, write_only=True)
    order_products_detail = OrderProductSerializer(source="order_products", many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "address",
            "subtotal",
            "discount_amount",
            "delivery_amount",
            "total_payment",
            "used_point",
            "order_status",
            "delivery_status",
            "order_products",
            "order_products_detail",
            "created_at",
        ]
        read_only_fields = ["order_number", "order_status", "delivery_status", "created_at"]

    def validate(self, data):
        if data.get("discount_amount", 0) < 0:
            raise serializers.ValidationError("할인 금액은 0보다 작을 수 없습니다.")
        if data.get("used_point", 0) < 0:
            raise serializers.ValidationError("사용 포인트는 0보다 작을 수 없습니다.")

        request = self.context.get("request")
        if request and "address" in data and data["address"].user != request.user:
            raise serializers.ValidationError("본인 주소만 선택할 수 있습니다.")

        return data

    def create(self, validated_data):
        order_products_data = validated_data.pop("order_products", [])
        order = Order.objects.create(**validated_data)

        subtotal = 0
        for item in order_products_data:
            product = item["product"]
            amount = item.get("amount", 1)
            price = product.product_value
            total_price = price * amount

            OrderProduct.objects.create(
                order=order,
                product=product,
                amount=amount,
                price=price,
                total_price=total_price,
            )
            subtotal += total_price

        order.subtotal = subtotal
        order.total_payment = subtotal - order.discount_amount + order.delivery_amount
        order.save()
        return order
