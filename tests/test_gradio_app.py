from unittest import TestCase
from unittest.mock import MagicMock

from highwind.client import Client
from highwind.client_factory import ClientFactory
from highwind.gradio_app import GradioApp


class TestGradioApp(TestCase):
    def setUp(self) -> None:
        # Clear the ClientFactory.client_singleton cached variable:
        ClientFactory.client_singleton = None

    def test_setup_with_request_returns_none_if_session_middleware_is_not_used(self):
        mock_session: MagicMock = MagicMock()
        mock_session.get.side_effect = AssertionError
        mock_gradio_request: MagicMock = MagicMock()
        mock_gradio_request.session = mock_session

        result = GradioApp.setup_with_request(mock_gradio_request)
        assert result is None

    def test_setup_with_request_returns_none_if_the_access_token_is_not_present_in_the_session(
        self,
    ):
        mock_session: MagicMock = MagicMock()
        mock_session.get.return_value = None
        mock_gradio_request: MagicMock = MagicMock()
        mock_gradio_request.session = mock_session

        result = GradioApp.setup_with_request(mock_gradio_request)
        assert result is None

    def test_setup_with_request_returns_a_highwind_client_with_the_access_token_if_the_access_token_is_present_in_the_session(
        self,
    ):
        mock_token: str = "super-secret-token-123"

        mock_session: MagicMock = MagicMock()
        mock_session.get.return_value = mock_token
        mock_gradio_request: MagicMock = MagicMock()
        mock_gradio_request.session = mock_session

        client = GradioApp.setup_with_request(mock_gradio_request)

        assert client is not None
        assert isinstance(client, Client)
        assert client.access_token == mock_token
