import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

import base64
import hashlib
import os
from urllib.parse import urlencode


class ClientCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/callback" in self.path:
            query_components = self.path.split("?", 1)[1]
            query_params = dict(qc.split("=") for qc in query_components.split("&"))
            self.server.auth_code = query_params.get("code")
            self.server.state = query_params.get("state")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"You can close this window now.")


class Client:
    """
    Low-level client for HTTP communication with Highwind
    """

    def __init__(self):
        self.highwind_api_url = os.environ.get("HIGHWIND_API_URL")
        self.highwind_auth_url = os.environ.get("HIGHWIND_AUTH_URL")
        self.highwind_auth_realm_id = os.environ.get("HIGHWIND_AUTH_REALM_ID")
        self.highwind_auth_client_id = os.environ.get("HIGHWIND_AUTH_CLIENT_ID")
        self.highwind_auth_redirect_uri = os.environ.get("HIGHWIND_AUTH_REDIRECT_URI")

    def login(self) -> bool:
        """
        Attempt to login and exchange a code for an auth token
        """
        auth_url, code_verifier = self._generate_auth_url()
        print("Please navigate here to authenticate:")
        print(auth_url)
        auth_code, state = self.get_auth_code()

        print(f"{auth_code=}")
        print(f"{state=}")

        token = self.get_token(auth_code, code_verifier)

        print(token)

        access_token: str = token["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{self.highwind_api_url}/users/me/", headers=headers)
        print(response.status_code)
        print(response.json())

    def get_auth_code(self) -> Tuple[str, str]:
        server = HTTPServer(("localhost", 8000), ClientCallbackHandler)
        server.handle_request()
        return server.auth_code, server.state

    def get_token(self, auth_code, code_verifier):
        token_url = f"{self.highwind_auth_url}/realms/{self.highwind_auth_realm_id}/protocol/openid-connect/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.highwind_auth_client_id,
            "code": auth_code,
            "redirect_uri": self.highwind_auth_redirect_uri,
            "code_verifier": code_verifier,
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()

    def _generate_auth_url(self) -> Tuple[str, bytes]:
        code_verifier, code_challenge = self._generate_pkce()
        params = {
            "client_id": self.highwind_auth_client_id,
            "response_type": "code",
            "scope": "openid",
            "redirect_uri": self.highwind_auth_redirect_uri,
            "state": str(uuid.uuid4()),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url: str = (
            f"{self.highwind_auth_url}/realms/{self.highwind_auth_realm_id}/protocol/openid-connect/auth?{urlencode(params)}"
        )

        return auth_url, code_verifier

    def _generate_pkce(self) -> Tuple[bytes, bytes]:
        """
        Keycloak is configured with authorization Code Flow with PKCE (Proof Key for
        Code Exchange).

        Returns a two-tuple of:
            1. code_verifier
            2. code_challenge
        """
        code_verifier: bytes = (
            base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
        )
        code_challenge: bytes = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode("utf-8")
            .rstrip("=")
        )
        return code_verifier, code_challenge
