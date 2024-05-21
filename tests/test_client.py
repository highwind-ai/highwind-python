from highwind.client import Client


class TestClient:
    def test_login_begins_a_login_flow_by_giving_the_user_a_login_url_and_starting_an_http_server_to_listen_for_the_callback(
        self, mock_auth_callback_server
    ):
        client: Client = Client()
        login_result: bool = client.login()

        mock_auth_callback_server.assert_called_with(
            ("localhost", 8000),
            Client.ClientCallbackHandler,
            bind_and_activate=True,
        )

        assert login_result is True
