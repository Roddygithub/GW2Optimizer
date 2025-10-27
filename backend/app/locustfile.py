"""
Initial load testing script for GW2Optimizer using Locust.

This script simulates user behavior for registration and login.

To run:
1. Make sure the backend server is running.
2. Run `locust -f locustfile.py --host http://localhost:8000`
3. Open your browser to http://localhost:8089
"""

try:
    from locust import HttpUser, task, between
except ImportError:  # pragma: no cover - optional dependency for load testing
    class HttpUser:  # type: ignore[override]
        """Fallback HttpUser to allow documentation builds without locust."""

        wait_time = None

    def task(func):  # type: ignore[misc]
        """Fallback task decorator when locust is unavailable."""

        return func

    def between(min_wait, max_wait):  # type: ignore[unused-argument]
        """Fallback wait time factory when locust is unavailable."""

        def _wait_time():
            return min_wait

        return _wait_time

try:
    from faker import Faker
except ImportError:  # pragma: no cover - optional dependency for docs builds
    class Faker:  # type: ignore[override]
        """Minimal Faker replacement for documentation builds."""

        def user_name(self) -> str:  # type: ignore[override]
            return "testuser"

        def email(self) -> str:  # type: ignore[override]
            return "test@example.com"

fake = Faker()


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """On start, create a user and log in."""
        self.username = fake.user_name()
        self.email = fake.email()
        self.password = "ValidPassword!123"
        self.register()
        self.login()

    def register(self):
        self.client.post(
            "/api/v1/auth/register", json={"email": self.email, "username": self.username, "password": self.password}
        )

    @task
    def login(self):
        self.client.post("/api/v1/auth/token", data={"username": self.email, "password": self.password})
