from typing import Dict
from unittest.mock import patch

import pytest
import requests_mock


@pytest.fixture(autouse=True)
def mock_auth_callback_server():
    with patch("highwind.client.HTTPServer") as mock_auth_callback_server:
        yield mock_auth_callback_server


@pytest.fixture(autouse=True)
def mock_token_endpoint():
    with requests_mock.Mocker() as mock_token_endpoint:
        mock_token: Dict = {"access_token": "access-token-123"}
        mock_token_endpoint.post(
            "https://keycloak.dev.highwind.cloud/realms/highwind-realm/protocol/openid-connect/token",
            json=mock_token,
        )

        yield mock_token_endpoint
