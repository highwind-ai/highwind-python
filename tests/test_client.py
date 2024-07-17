from highwind.client import Client


class TestClient:
    def test_login_begins_a_login_flow_by_starting_an_http_server_to_listen_for_the_callback(
        self, mock_auth_callback_server
    ):
        client: Client = Client()
        assert client.login() is True

        mock_auth_callback_server.assert_called_with(
            ("localhost", 8000),
            Client.ClientCallbackHandler,
            bind_and_activate=True,
        )

    def test_login_sets_the_clients_access_token(self):
        client: Client = Client()
        assert client.access_token is None
        assert client.login() is True
        assert client.access_token == "access-token-123"

    def test_can_be_initialized_with_an_existing_token(self, mock_auth_callback_server):
        existing_token: str = "my-existing-token-123"
        client: Client = Client(access_token=existing_token)
        assert client.is_logged_in()

        mock_auth_callback_server.assert_not_called()
