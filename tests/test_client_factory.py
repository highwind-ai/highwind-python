from highwind.client import Client
from highwind.client_factory import ClientFactory


class TestClientFactory:
    def test_client_creates_and_returns_a_memoized_client(self):
        client_1 = ClientFactory.client()
        assert isinstance(client_1, Client)

        client_2 = ClientFactory.client()
        assert isinstance(client_2, Client)

        # Assert client_1 and client_2 exist in the same space in memory
        # (i.e. they are the exact same instance of the Client class)
        assert id(client_1) == id(client_2)
