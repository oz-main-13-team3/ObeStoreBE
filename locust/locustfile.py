from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 유저 로그인
        resp = self.client.post(
            "/oauth/login",
            json={"email": "test@test.com", "password": "test1234"},
        )
        self.jwt = resp.json()["access"]
        self.headers = {"Authorization": f"Bearer {self.jwt}"}

    @task
    def get_products(self):
        self.client.get("/products", headers=self.headers)
