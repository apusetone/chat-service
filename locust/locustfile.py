from locust import HttpUser, between, task


class MyUser(HttpUser):
    wait_time = between(0.01, 0.03)

    _refresh_token = None
    _chat_id = 1
    _message_id = 1

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.post(
            "/api/auth/login", json={"email": "user@example.com"}
        )
        token = response.json().get("token")
        response = self.client.post(
            "/api/auth/2fa", json={"code": "999999", "token": token}
        )
        response_result = response.json()
        access_token = response_result["access_token"]
        self._refresh_token = response_result["refresh_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    @task
    def get_user(self):
        self.client.get("/api/users")

    @task
    def update_user(self):
        self.client.put(
            "/api/users",
            json={
                "is_name_visible": False,
                "username": "testuser12345",
                "first_name": "John",
                "last_name": "Smith",
                "new_email": None,
                "notification_type": "mobile_push",
            },
        )

    @task
    def get_all_chats(self):
        self.client.get(
            "/api/chats?offset=0&limit=10&desc=true",
        )

    @task
    def create_chat(self):
        response = self.client.post(
            "/api/chats",
            json={
                "name": "New room",
                "participant_names": ["user1", "user2", "user3"],
            },
        )
        response_result = response.json()
        self._chat_id = response_result["id"]

    @task
    def get_chat_participants(self):
        self.client.get(
            f"/api/chats/{self._chat_id}/participants",
        )

    @task
    def get_all_messages(self):
        self.client.get(
            f"/api/messages/chat/{self._chat_id}?offset=0&limit=10",
        )

    @task
    def create_message(self):
        response = self.client.post(
            f"/api/messages/chat/{self._chat_id}",
            json={"content": "Sample message"},
        )
        response_result = response.json()
        self._message_id = response_result["id"]

    @task
    def delete_message(self):
        self.client.delete(f"/api/messages/{self._message_id}")
