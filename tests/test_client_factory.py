from unittest import TestCase

from highwind.client import Client
from highwind.client_factory import ClientFactory


class TestClientFactory(TestCase):
    def setUp(self) -> None:
        # Clear the ClientFactory.client_singleton cached variable:
        ClientFactory.client_singleton = None

    def test_get_client_creates_and_returns_a_memoized_client(self):
        client_1 = ClientFactory.get_client()
        assert isinstance(client_1, Client)

        assert id(ClientFactory.client_singleton) == id(client_1)

        client_2 = ClientFactory.get_client()
        assert isinstance(client_2, Client)

        # Assert client_1 and client_2 exist in the same space in memory
        # (i.e. they are the exact same instance of the Client class)
        assert id(client_1) == id(client_2)

    def test_get_client_can_create_a_client_without_an_access_token(self):
        access_token: str = "secret-token-123"

        client = ClientFactory.get_client(access_token=access_token)
        assert client.access_token == access_token

    def test_get_client_can_create_a_client_with_an_access_token(self):
        client = ClientFactory.get_client()
        assert client.access_token is None
