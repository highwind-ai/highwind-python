import json
from unittest.mock import patch

from freezegun import freeze_time

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

    @freeze_time("2012-01-14 03:21:34", tz_offset=0)
    def test_login_sets_the_clients_access_token_refresh_token_and_token_expiry(self):
        client: Client = Client()

        assert client.access_token is None
        assert client.refresh_token is None
        assert client.token_expiry is None

        assert client.login() is True

        assert client.access_token == "access-token-123"
        assert client.refresh_token == "refresh-token-123"
        assert client.token_expiry == "2012-01-14T03:26:34"  # 300 seconds from now

    def test_can_be_initialized_with_an_existing_access_token_refresh_token_and_token_expiry(
        self, mock_auth_callback_server
    ):
        existing_access_token: str = "my-existing-access-token-123"
        existing_refresh_token: str = "my-existing-refresh-token-123"
        existing_token_expiry: str = "2012-01-14T03:26:34"

        client: Client = Client(
            access_token=existing_access_token,
            refresh_token=existing_refresh_token,
            token_expiry=existing_token_expiry,
        )
        assert client.is_logged_in()

        mock_auth_callback_server.assert_not_called()

    @freeze_time("2012-01-14 03:20:00", tz_offset=0)
    def test_get_will_log_in_if_not_logged_in_already(self, mock_api):
        use_case_id: str = "d84258c7-b531-4ee8-8aca-639658c189c8"

        with open("tests/fixtures/deployed_use_case.json") as fixture:
            mock_use_case = json.load(fixture)

        mock_api.get(
            f"https://api.zindi.highwind.cloud/api/v1/use_cases/mine/{use_case_id}/",
            json=mock_use_case,
        )

        client: Client = Client()

        assert client.is_logged_in() is False
        assert client.access_token is None
        assert client.refresh_token is None
        assert client.token_expiry is None

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        assert client.is_logged_in()
        assert client.access_token == "access-token-123"
        assert client.refresh_token == "refresh-token-123"
        assert client.token_expiry == "2012-01-14T03:25:00"  # 5 minutes from now

        login_spy.assert_called_once()
        refresh_token_spy.assert_not_called()

    @freeze_time("2012-01-14 01:00:00", tz_offset=0)
    def test_get_will_not_log_in_if_already_logged_in_and_token_is_not_expired(
        self, mock_api
    ):
        use_case_id: str = "d84258c7-b531-4ee8-8aca-639658c189c8"

        with open("tests/fixtures/deployed_use_case.json") as fixture:
            mock_use_case = json.load(fixture)

        mock_api.get(
            f"https://api.zindi.highwind.cloud/api/v1/use_cases/mine/{use_case_id}/",
            json=mock_use_case,
        )

        client: Client = Client(
            access_token="access-token-123",
            refresh_token="refresh-token-123",
            token_expiry="2012-01-14T01:05:00",  # 5 minutes from now
        )

        assert client.is_logged_in() is True

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        login_spy.assert_not_called()
        refresh_token_spy.assert_not_called()

    @freeze_time("2012-01-14 01:10:00", tz_offset=0)
    def test_get_will_attempt_to_refresh_token_if_token_is_expired(self, mock_api):
        use_case_id: str = "d84258c7-b531-4ee8-8aca-639658c189c8"

        with open("tests/fixtures/deployed_use_case.json") as fixture:
            mock_use_case = json.load(fixture)

        mock_api.get(
            f"https://api.zindi.highwind.cloud/api/v1/use_cases/mine/{use_case_id}/",
            json=mock_use_case,
        )

        client: Client = Client(
            access_token="access-token-123",
            refresh_token="refresh-token-123",
            token_expiry="2012-01-14T01:05:00",  # 5 minutes ago
        )

        assert client.is_logged_in() is True

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        login_spy.assert_not_called()
        refresh_token_spy.assert_called_once()
