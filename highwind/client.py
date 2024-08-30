from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

import base64
import hashlib
import os
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import requests


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
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(
                    b"""
                    <html>
                    <head>
                        <script type="text/javascript">
                            window.onload = function() {
                                window.open('', '_self', '');
                                window.close();
                            };
                        </script>
                    </head>
                    <body>
                        Successfully authenticated with Highwind! You can now close this browser window.
                    </body>
                    </html>
                    """
                )

    # Fixed constants
    GRANT_TYPE: str = "authorization_code"
    REFRESH_GRANT_TYPE: str = "refresh_token"
    RESPONSE_TYPE: str = "code"
    CODE_CHALLENGE_METHOD: str = "S256"
    TIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"

    # Constants read from environment variables with default fallbacks:
    AUTOMATICALLY_OPEN_BROWSER: bool = (
        os.environ.get("AUTOMATICALLY_OPEN_BROWSER", "True") == "True"
    )
    LOCALHOST_AUTH_CALLBACK_PORT: str = os.environ.get(
        "LOCALHOST_AUTH_CALLBACK_PORT",
        default="8000",
    )
    HIGHWIND_API_URL: str = os.environ.get(
        "HIGHWIND_API_URL",
        default="https://api.zindi.highwind.cloud/api/v1",
    )
    HIGHWIND_AUTH_URL: str = os.environ.get(
        "HIGHWIND_AUTH_URL",
        default="https://keycloak.zindi.highwind.cloud",
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

    def __init__(
        self,
        access_token: Optional[str] = None,
        access_token_expires_in: float = 0,
        access_token_expires_at: Optional[str] = None,
        refresh_token: Optional[str] = None,
        refresh_token_expires_in: float = 0,
        refresh_token_expires_at: Optional[str] = None,
    ):
        self.access_token: Optional[str] = access_token
        self.access_token_expires_in: float = access_token_expires_in
        self.access_token_expires_at: Optional[str] = access_token_expires_at
        self.refresh_token: Optional[str] = refresh_token
        self.refresh_token_expires_in: float = refresh_token_expires_in
        self.refresh_token_expires_at: Optional[str] = refresh_token_expires_at

    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict:
        """
        Performs an HTTP GET to the Highwind API.

        Raises an HTTPError if there is one.

        Returns a Dictionary of whatever JSON the Highwind API returns, if the response
        is successful.
        """
        self._authenticate()

        full_url: str = f"{Client.HIGHWIND_API_URL}/{url}/"
        headers: Dict = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url=full_url, params=params, data=data, headers=headers)
        response.raise_for_status()

        return response.json()

    def login(self) -> bool:
        """
        Begins a login flow.

        Users HAVE to authenticate on Highwind's auth provider (Keycloak), and should
        NEVER provide username and password to the SDK directly.

        Outputs a URL for the user of the SDK to authenticate with Highwind and starts
        an HTTPServer to listen for a localhost callback.

        If AUTOMATICALLY_OPEN_BROWSER is set to 'True', will automatically open the
        User's default web browser and navigate to the authentication URL.

        Returns True upon successful login

        Also sets `access_token`, `refresh_token`, `access_token_expires_in`,
        `refresh_token_expires_in`, `access_token_expires_at`, and
        `refresh_token_expires_at`.
        """
        auth_url, code_verifier = self._generate_auth_url()
        self._print_auth_url(auth_url)

        if Client.AUTOMATICALLY_OPEN_BROWSER:
            self._automatically_open_url(auth_url)

        (auth_code, _state) = self._start_server_to_listen_for_auth_code()

        token: Dict[str, str] = self._get_access_token(auth_code, code_verifier)

        self._set_variables_from_token(token)

        if not self.access_token:
            raise Exception(
                "Token received from Keycloak did not contain 'access_token': "
                + str(token)
            )

        return True

    def _authenticate(self) -> None:
        """
        Performs the authentication flow.

        1. If there is no access token, performs the login flow.
        2. If there is an access token and it is not expired, does nothing.
        3. If there is an expired access token, but a valid refresh token, performs the
           refresh token flow.
        4. If there is an expired refresh token, raises an exception.
        """
        if not self.access_token:
            self.login()
        elif self.access_token and not self._is_access_token_expired():
            return
        elif self._is_access_token_expired() and not self._is_refresh_token_expired():
            self._refresh_access_token()
        elif self._is_refresh_token_expired():
            raise Exception("Please refresh your login.")

    def _is_access_token_expired(self) -> bool:
        """
        Checks if the access token is expired.
        """
        if self.access_token_expires_in == 0:
            return False  # Access token is non-expiring

        return self._is_token_expired(self.access_token_expires_at)

    def _is_refresh_token_expired(self) -> bool:
        """
        Checks if the refresh token is expired.
        """
        if self.refresh_token_expires_in == 0:
            return False  # Refresh token is non-expiring

        return self._is_token_expired(self.refresh_token_expires_at)

    def _is_token_expired(self, timestamp: Optional[str]) -> bool:
        if not timestamp:
            return True  # If the token expiry is not set, it is assumed to have expired

        now: datetime = datetime.now(tz=timezone.utc)
        expiry: datetime = datetime.strptime(timestamp, self.TIME_FORMAT).replace(
            tzinfo=timezone.utc
        )

        return expiry <= now

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

    def _get_access_token(self, auth_code, code_verifier) -> Dict:
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

    def _refresh_access_token(self):
        refresh_token_url: str = (
            f"{Client.HIGHWIND_AUTH_URL}/realms/{Client.HIGHWIND_AUTH_REALM_ID}/protocol/openid-connect/token"
        )

        data: Dict[str, str] = {
            "grant_type": Client.REFRESH_GRANT_TYPE,
            "client_id": Client.HIGHWIND_AUTH_CLIENT_ID,
            "refresh_token": self.refresh_token,
        }

        response = requests.post(refresh_token_url, data=data)
        response.raise_for_status()  # Raises an HTTPError if one occurred

        token: Dict[str, str] = response.json()

        self._set_variables_from_token(token)

    def _generate_auth_url(self) -> Tuple[str, str]:
        """
        Generates an expiring authentication URL that the user of the SDK can follow to
        complete authentication with Highwind's auth provider (Keycloak).

        The auth URL will look something like this:

        "https://keycloak.zindi.highwind.cloud/realms/highwind-realm/protocol/openid-connect/auth
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

    def _automatically_open_url(self, auth_url: str) -> None:
        webbrowser.open(auth_url)

    def _set_variables_from_token(self, token: Dict[str, str]) -> None:
        """
        Given an Oauth2 Token in dictionary form, sets the Client's:
            1. access_token
            2. access_token_expires_in
            3. access_token_expires_at
            4. refresh_token
            5. refresh_token_expires_in
            6. refresh_token_expires_at
        """
        expires_in: float = float(dict(token).get("expires_in", 0))
        refresh_expires_in: float = float(dict(token).get("refresh_expires_in", 0))

        self.access_token = token.get("access_token", None)
        self.access_token_expires_in = expires_in
        self.access_token_expires_at = self._calculate_token_expiry(expires_in)

        self.refresh_token = token.get("refresh_token", None)
        self.refresh_token_expires_in = refresh_expires_in
        self.refresh_token_expires_at = self._calculate_token_expiry(refresh_expires_in)

    def _calculate_token_expiry(self, expires_in: float) -> str:
        return (
            datetime.now(tz=timezone.utc) + timedelta(seconds=float(expires_in))
        ).strftime(self.TIME_FORMAT)
