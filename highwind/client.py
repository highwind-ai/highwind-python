import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

import base64
import hashlib
import os
from urllib.parse import urlencode


class Client:
    """
    Low-level client for HTTP communication with Highwind.
    """

    # Helper class
    class ClientCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if "/callback" in self.path:
                query_components = self.path.split("?", 1)[1]
                query_params = dict(qc.split("=") for qc in query_components.split("&"))

                self.server.auth_code = query_params.get("code")  # type: ignore
                self.server.state = query_params.get("state")  # type: ignore

                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b"Successfully authenticated with Highwind! You can now close this browser window."
                )

    # Fixed constants
    GRANT_TYPE: str = "authorization_code"
    RESPONSE_TYPE: str = "code"
    CODE_CHALLENGE_METHOD: str = "S256"

    # Constants read from environment variables with default fallbacks:
    LOCALHOST_AUTH_CALLBACK_PORT: str = os.environ.get(
        "LOCALHOST_AUTH_CALLBACK_PORT",
        default="8000",
    )
    HIGHWIND_API_URL: str = os.environ.get(
        "HIGHWIND_API_URL",
        default="https://api.dev.highwind.cloud/api/v1",
    )
    HIGHWIND_AUTH_URL: str = os.environ.get(
        "HIGHWIND_AUTH_URL",
        default="https://keycloak.dev.highwind.cloud",
    )
    HIGHWIND_AUTH_REALM_ID: str = os.environ.get(
        "HIGHWIND_AUTH_REALM_ID",
        default="highwind-realm",
    )
    HIGHWIND_AUTH_CLIENT_ID: str = os.environ.get(
        "HIGHWIND_AUTH_CLIENT_ID",
        default="highwind-sdk",
    )
    HIGHWIND_AUTH_REDIRECT_URI: str = os.environ.get(
        "HIGHWIND_AUTH_REDIRECT_URI",
        default="http://localhost:8000/callback",
    )

    def __init__(self):
        pass  # TODO: CHECK FOR CORRECT CONFIGURATION

    def login(self) -> bool:
        """
        Begins a login flow.

        Users HAVE to authenticate on Highwind's auth provider (Keycloak), and should
        NEVER provide username and password to the SDK directly.

        Outputs a URL for the user of the SDK to authenticate with Highwind and starts
        an HTTPServer to listen for a localhost callback.

        Returns True upon successful login
        """
        auth_url, code_verifier = self._generate_auth_url()
        self._print_auth_url(auth_url)

        (auth_code, _state) = self._start_server_to_listen_for_auth_code()

        token: Dict[str, str] = self._get_token(auth_code, code_verifier)

        access_token: str = token.get("access_token", "")

        if not access_token:
            raise Exception(
                "Token received from Keycloak did not contain 'access_token': "
                + str(token)
            )

        return True

    def _start_server_to_listen_for_auth_code(self) -> Tuple[str, str]:
        """
        Starts an HTTPServer running on localhost and (by default) port 8000 to listen
        for the Keycloak callback.

        Returns a two-tuple of:
            1. auth_code: str   (This is the code that will be exchanged with Keycloak
                                for a valid auth token)
            2. state: str       (Currently unused)
        """
        server = HTTPServer(
            ("localhost", int(Client.LOCALHOST_AUTH_CALLBACK_PORT)),
            Client.ClientCallbackHandler,
            bind_and_activate=True,
        )

        server.handle_request()  # Starts the server and awaits a callback from Keycloak

        return (server.auth_code, server.state)  # type: ignore

    def _get_token(self, auth_code, code_verifier) -> Dict:
        """
        Exchanges an auth_code (str) with Keycloak to get a valid auth token.

        Returns a Dictionary containing the following keys:
            1. access_token (this is the token that the Client will use for all subsequent API calls)
            2. expires_in
            3. refresh_expires_in
            4. refresh_token
            5. token_type
            6. id_token
            7. not-before-policy
            8. session_state
            9. scope
        """
        token_url: str = (
            f"{Client.HIGHWIND_AUTH_URL}/realms/{Client.HIGHWIND_AUTH_REALM_ID}/protocol/openid-connect/token"
        )

        data: Dict[str, str] = {
            "grant_type": Client.GRANT_TYPE,
            "client_id": Client.HIGHWIND_AUTH_CLIENT_ID,
            "code": auth_code,
            "redirect_uri": Client.HIGHWIND_AUTH_REDIRECT_URI,
            "code_verifier": code_verifier,
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raises an HTTPError if one occurred

        return response.json()

    def _generate_auth_url(self) -> Tuple[str, str]:
        """
        Generates an expiring authentication URL that the user of the SDK can follow to
        complete authentication with Highwind's auth provider (Keycloak).

        The auth URL will look something like this:

        "https://keycloak.dev.highwind.cloud/realms/highwind-realm/protocol/openid-connect/auth
        ?client_id=highwind-sdk
        &response_type=code
        &scope=openid
        &redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback
        &state=54b...0c8
        &code_challenge=dBDC...Y8h4
        &code_challenge_method=S256"

        Returns a two-tuple of:
            1. auth_url: str
            2. code_verifier: str
        """
        (code_verifier, code_challenge) = self._generate_pkce()

        params = {
            "client_id": Client.HIGHWIND_AUTH_CLIENT_ID,
            "response_type": "code",
            "scope": "openid",
            "redirect_uri": Client.HIGHWIND_AUTH_REDIRECT_URI,
            "state": str(uuid.uuid4()),
            "code_challenge": code_challenge,
            "code_challenge_method": Client.CODE_CHALLENGE_METHOD,
        }

        auth_url: str = (
            f"{Client.HIGHWIND_AUTH_URL}/realms/{Client.HIGHWIND_AUTH_REALM_ID}/protocol/openid-connect/auth?{urlencode(params)}"
        )

        return (auth_url, code_verifier)

    def _generate_pkce(self) -> Tuple[str, str]:
        """
        Keycloak is configured with authorization Code Flow with PKCE (Proof Key for
        Code Exchange).

        Returns a two-tuple of:
            1. code_verifier: str
            2. code_challenge: str
        """
        code_verifier: str = (
            base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
        )
        code_challenge: str = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode("utf-8")
            .rstrip("=")
        )

        return (code_verifier, code_challenge)

    def _print_auth_url(self, auth_url: str) -> None:
        """
        Simply displays the auth URL to the User of the SDK.
        """
        print("+---------------------------------------------------------------------+")
        print("| Please navigate to the following URL to authenticate with Highwind: |")
        print("+---------------------------------------------------------------------+")
        print(auth_url)
        print("")
