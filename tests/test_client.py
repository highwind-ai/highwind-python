from unittest import TestCase

from highwind.client import Client


class TestClient(TestCase):
    def test_login_attempts_a_login_flow(self):
        client: Client = Client()
        client.login()
