"""
Initial load testing script for GW2Optimizer using Locust.

This script simulates user behavior for registration and login.

To run:
1. Make sure the backend server is running.
2. Run `locust -f locustfile.py --host http://localhost:8000`
3. Open your browser to http://localhost:8089
"""

from locust import HttpUser, task, between
from faker import Faker

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
