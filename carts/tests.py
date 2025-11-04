from django.test import TestCase
from users.models import User
from products.models import Product, Category, Tag, Brand
from carts.models import Cart, CartItem


class CartModelTest(TestCase):
    def setUp(self):
        # 유저 생성
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword",
            username="테스트유저",
            nickname="testnick",
            phone_number="01012345678",
        )

        # 카테고리, 태그, 브랜드 생성
        self.category = Category.objects.create(category_name="테스트카테고리")
        self.tag = Tag.objects.create(tag_name="테스트태그")
        self.brand = Brand.objects.create(brand_name="테스트브랜드")

        # 상품 생성
        self.product = Product.objects.create(
            product_name="테스트 상품",
            product_value=10000,
            product_stock=10,
            category=self.category,
            tag=self.tag,
            brand=self.brand,
        )

        # 장바구니 생성
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        """장바구니가 정상적으로 생성되는지 확인"""
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(str(self.cart), f"{self.user.nickname}의 카트")

    def test_add_cart_item(self):
        """장바구니에 상품을 추가할 수 있는지 확인"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            amount=2,
        )

        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.amount, 2)
        self.assertEqual(
            str(cart_item),
            f"[{self.cart.user.nickname} 카트] {self.product.product_name} 상품 | {cart_item.amount} 개",
        )

    def test_cart_item_null_safety(self):
        """상품이 삭제되어도 장바구니 아이템 접근에 문제가 없는지 확인"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            amount=1,
        )
        self.product.delete()
        cart_item.refresh_from_db()

        self.assertIsNone(cart_item.product)
        self.assertEqual(cart_item.amount, 1)

    def test_add_duplicate_cart_item_increases_amount(self):
        """동일 상품을 추가하면 수량만 증가하는지 확인"""
        # 첫 번째 추가
        CartItem.objects.create(cart=self.cart, product=self.product, amount=2)

        # 두 번째 추가 (중복)
        cart_item, created = CartItem.objects.get_or_create(cart=self.cart, product=self.product)
        if not created:
            cart_item.amount += 3
            cart_item.save()

        # 실제 수량 확인
        self.assertEqual(CartItem.objects.filter(cart=self.cart, product=self.product).count(), 1)
        self.assertEqual(CartItem.objects.get(cart=self.cart, product=self.product).amount, 5)