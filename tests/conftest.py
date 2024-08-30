from typing import Dict
from unittest.mock import patch

import pytest
import requests_mock


@pytest.fixture(autouse=True)
def mock_auth_callback_server():
    with patch("highwind.client.HTTPServer") as mock_auth_callback_server:
        yield mock_auth_callback_server


@pytest.fixture(autouse=True)
def mock_api():
    with requests_mock.Mocker() as mock_api:
        mock_token: Dict = {
            "access_token": "access-token-123",
            "expires_in": 300,  # 5 minutes
            "refresh_expires_in": 1200,  # 20 minutes
            "refresh_token": "refresh-token-123",
            "token_type": "Bearer",
            "id_token": "id-token-123",
            "not-before-policy": 0,
            "session_state": "df905c8d-9ce5-45cb-b8ca-f964ddd7337e",
            "scope": "openid offline_access profile email",
        }
        mock_api.post(
            "https://keycloak.zindi.highwind.cloud/realms/highwind-realm/protocol/openid-connect/token",
            json=mock_token,
        )

        yield mock_api


@pytest.fixture(autouse=True)
def mock_web_browser():
    with patch("highwind.client.webbrowser"):
        yield  # Prevents opening a browser when running tests
