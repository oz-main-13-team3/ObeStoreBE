from django.test import TestCase

from products.models import Brand, Category, Product, Tag
from reviews.models import Keyword, Review, ReviewKeyword
from users.models import User


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="1234",
            nickname="nick",
            username="테스트",
        )

        self.category = Category.objects.create(category_name="카테고리")
        self.brand = Brand.objects.create(brand_name="브랜드")
        self.tag = Tag.objects.create(tag_name="태그")

        self.product = Product.objects.create(
            product_name="테스트 상품",
            product_value="1000",
            product_stock="5",
            category=self.category,
            brand=self.brand,
            tag=self.tag,
        )

        self.keyword = Keyword.objects.create(
            keyword_name="갓성비",
            keyword_type="긍정",
        )

        self.review = Review.objects.create(
            review_title="이런 상품 어디서 구매 못합니다.",
            content=(
                """오브 스토어에서 처음보는 상품입니다. 
								저만 믿고 구매 해보세요, 
								후회 안합니다. 
								아..별점이 5점까지만 있는게 많이 아쉽네요!"""
            ),
            rating="5",
            product=self.product,
            user=self.user,
        )

    def test_review_creation(self):
        self.assertEqual(self.review.review_title, "이런 상품 어디서 구매 못합니다.")
        self.assertEqual(self.review.rating, "5")
        self.assertEqual(self.review.product, self.product)
        self.assertEqual(self.review.user, self.user)

    def test_review_keyword_relation(self):
        ReviewKeyword.objects.create(review=self.review, keyword=self.keyword)
        self.assertIn(self.keyword, self.review.keywords.all())
