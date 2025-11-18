import random

from locust import HttpUser, between, task


class WebUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3)

    VALID_PRODUCT_IDS = []
    VALID_QNA_IDS = []
    VALID_ORDER = [
        "sales", "-sales",
        "product_value", "-product_value",
        "created_at", "-created_at",
        "review_count", "-review_count",
    ]

    def on_start(self):
        payload = {
            "email": "naver@naver.com",
            "password": "gmail1423i",
        }
        resp = self.client.post("/auth/login", json=payload)

        if resp.status_code != 200:
            print("로그인 실패 → 테스트 중단:", resp.text)
            self.stop(True)
            return

        access = resp.json().get("access")
        self.headers = {"Authorization": f"Bearer {access}"}

        products = self.client.get("/products/").json()
        self.VALID_PRODUCT_IDS = [p["id"] for p in products]

        qnas = self.client.get("/qna/").json()
        self.VALID_QNA_IDS = [q["id"] for q in qnas]

    def _clean_query(self, q: dict):
        return {k: v for k, v in q.items() if v not in ["", None]}

    @task(3)
    def get_products(self):
        query = {
            "search": random.choice(["나이키", "아디다스", "신발"]),
            "min_price": random.choice([1000, None]),
            "max_price": random.choice([500000, None]),
            "ordering": random.choice(self.VALID_ORDER + [None]),
        }
        safe_query = self._clean_query(query)
        self.client.get("/products/", params=safe_query, headers=self.headers)

    @task(1)
    def product_details(self):
        if not self.VALID_PRODUCT_IDS:
            return
        product_id = random.choice(self.VALID_PRODUCT_IDS)
        self.client.get(f"/products/{product_id}/", headers=self.headers)

    @task(1)
    def review_list(self):
        self.client.get("/reviews/", headers=self.headers)

    @task(1)
    def review_create(self):
        if not self.VALID_PRODUCT_IDS:
            return

        payload = {
            "product": random.choice(self.VALID_PRODUCT_IDS),
            "review_title": "테스트 제목",
            "content": "리뷰 테스트 내용",
            "rating": random.choice([1.0, 2.0, 3.0, 4.0, 5.0]),  # decimal-safe
        }
        self.client.post("/reviews/", json=payload, headers=self.headers)

    @task(1)
    def qna_create(self):
        if not self.VALID_PRODUCT_IDS:
            return

        payload = {
            "product": random.choice(self.VALID_PRODUCT_IDS),
            "question_type": random.choice(["inquiry", "suggestion"]),  # API choices
            "question_title": "언제오나요?",
            "question_content": "배송 관련 문의 드립니다.",
        }
        self.client.post("/qna/", json=payload, headers=self.headers)

    @task(2)
    def qna_list(self):
        resp = self.client.get("/qna/", headers=self.headers)
        if resp.status_code == 200:
            data = resp.json()
            self.VALID_QNA_IDS = [q["id"] for q in data]

    @task(1)
    def qna_detail(self):
        if not self.VALID_QNA_IDS:
            return
        qna_id = random.choice(self.VALID_QNA_IDS)
        self.client.get(f"/qna/{qna_id}/", headers=self.headers)
