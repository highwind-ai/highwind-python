import json
from unittest.mock import patch

import pytest
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
    def test_login_sets_the_clients_authentication_details(self):
        client: Client = Client()

        assert client.access_token is None
        assert client.access_token_expires_in is 0
        assert client.access_token_expires_at is None
        assert client.refresh_token is None
        assert client.refresh_token_expires_in is 0
        assert client.refresh_token_expires_at is None

        assert client.login() is True

        assert client.access_token == "access-token-123"
        assert client.access_token_expires_in == 300
        assert client.access_token_expires_at == "2012-01-14T03:26:34"  # in 5 minutes

        assert client.refresh_token == "refresh-token-123"
        assert client.refresh_token_expires_in == 1200
        assert client.refresh_token_expires_at == "2012-01-14T03:41:34"  # in 20 minutes

    def test_can_be_initialized_with_an_existing_access_token_refresh_token_and_token_expiry(
        self, mock_auth_callback_server
    ):
        access_token: str = "my-existing-access-token-123"
        access_token_expires_in: int = 300
        access_token_expires_at: str = "2012-01-14T03:26:34"  # in 5 minutes

        refresh_token: str = "my-existing-refresh-token-123"
        refresh_token_expires_in: int = 1200
        refresh_token_expires_at: str = "2012-01-14T03:41:34"  # in 20 minutes

        Client(
            access_token=access_token,
            access_token_expires_in=access_token_expires_in,
            access_token_expires_at=access_token_expires_at,
            refresh_token=refresh_token,
            refresh_token_expires_in=refresh_token_expires_in,
            refresh_token_expires_at=refresh_token_expires_at,
        )

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

        assert client.access_token is None
        assert client.access_token_expires_in == 0
        assert client.access_token_expires_at is None
        assert client.refresh_token is None
        assert client.refresh_token_expires_in == 0
        assert client.refresh_token_expires_at is None

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        assert client.access_token == "access-token-123"
        assert client.access_token_expires_in == 300
        assert client.access_token_expires_at == "2012-01-14T03:25:00"
        assert client.refresh_token == "refresh-token-123"
        assert client.refresh_token_expires_in == 1200
        assert client.refresh_token_expires_at == "2012-01-14T03:40:00"

        login_spy.assert_called_once()
        refresh_token_spy.assert_not_called()

    @freeze_time("2012-01-14 01:00:00", tz_offset=0)
    def test_get_will_not_log_in_if_already_logged_in_and_access_token_is_not_expired(
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
            access_token_expires_in=300,
            access_token_expires_at="2012-01-14T01:05:00",  # 5 minutes from now
            refresh_token="refresh-token-123",
            refresh_token_expires_in=1200,
            refresh_token_expires_at="2012-01-14T01:20:00",  # 20 minutes from now
        )

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        login_spy.assert_not_called()
        refresh_token_spy.assert_not_called()

    @freeze_time("2012-01-14 01:10:00", tz_offset=0)
    def test_get_will_attempt_to_refresh_the_access_token_if_the_access_token_is_expired(
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
            access_token_expires_in=300,
            access_token_expires_at="2012-01-14T01:05:00",  # 5 minutes ago (EXPIRED)
            refresh_token="refresh-token-123",
            refresh_token_expires_in=1200,
            refresh_token_expires_at="2012-01-14T01:15:00",  # 5 minutes from now (NOT EXPIRED)
        )

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        login_spy.assert_not_called()
        refresh_token_spy.assert_called_once()

    @freeze_time("2012-01-14 03:00:00", tz_offset=0)
    def test_get_will_raise_an_exception_if_the_refresh_token_is_expired(
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
            access_token_expires_in=300,
            access_token_expires_at="2012-01-14T01:00:00",  # 1 hour ago (EXPIRED)
            refresh_token="refresh-token-123",
            refresh_token_expires_in=1200,
            refresh_token_expires_at="2012-01-14T02:00:00",  # 2 hours ago (EXPIRED)
        )

        with pytest.raises(Exception) as error:
            client.get(f"use_cases/mine/{use_case_id}")

        assert "Please refresh your login" in str(error.value)

    @freeze_time("2012-01-14 10:00:00", tz_offset=0)
    def test_get_will_not_attempt_to_refresh_non_expiring_access_token(self, mock_api):
        use_case_id: str = "d84258c7-b531-4ee8-8aca-639658c189c8"

        with open("tests/fixtures/deployed_use_case.json") as fixture:
            mock_use_case = json.load(fixture)

        mock_api.get(
            f"https://api.zindi.highwind.cloud/api/v1/use_cases/mine/{use_case_id}/",
            json=mock_use_case,
        )

        client: Client = Client(
            access_token="access-token-123",
            access_token_expires_in=0,  # Expires in 0 means non-expiring
            access_token_expires_at="2012-01-14T09:00:00",  # 1 hour ago (technically expired - but is a non-expiring token)
            refresh_token="refresh-token-123",
            refresh_token_expires_in=0,  # Expires in 0 means non-expiring
            refresh_token_expires_at="2012-01-14T09:30:00",  # 30 minutes ago (technically expired - but is a non-expiring token)
        )

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        login_spy.assert_not_called()
        refresh_token_spy.assert_not_called()

    @freeze_time("2012-01-14 14:00:00", tz_offset=0)
    def test_get_will_not_raise_an_exception_if_the_refresh_token_does_not_expire(
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
            access_token_expires_in=300,
            access_token_expires_at="2012-01-14T13:50:00",  # 10 minutes ago (EXPIRED)
            refresh_token="refresh-token-123",
            refresh_token_expires_in=0,  # Expires in 0 means non-expiring
            refresh_token_expires_at="2012-01-14T13:55:00",  # 5 minutes ago (technically expired - but is a non-expiring token)
        )

        with patch.object(client, "login", wraps=client.login) as login_spy:
            with patch.object(
                client, "_refresh_access_token", wraps=client._refresh_access_token
            ) as refresh_token_spy:
                client.get(f"use_cases/mine/{use_case_id}")

        login_spy.assert_not_called()
        refresh_token_spy.assert_called_once()
