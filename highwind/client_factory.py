from typing import Optional

from .client import Client


class ClientFactory:
    """
    Factory to return a singleton instance of a Client
    """

    client_singleton: Optional[Client] = None

    @classmethod
    def get_client(
        cls,
        force_recreate: bool = False,
        access_token: Optional[str] = None,
        access_token_expires_in: float = 0,
        access_token_expires_at: Optional[str] = None,
        refresh_token: Optional[str] = None,
        refresh_token_expires_in: float = 0,
        refresh_token_expires_at: Optional[str] = None,
    ) -> Client:
        """
        Gets the existing Highwind Client if present, or creates one.

        Parameters:
            - force_recreate: if True, the client will be recreated even if it already
              exists. If False, the existing client will be returned.

            - access_token: this is an optional access_token string that can be passed
              if a valid JWT is known. If one is not known, the user will be prompted to
              log into Highwind on the first API call.

            - access_token_expires_in: float of number of seconds until the access token
              expires

            - access_token_expires_at: optional string in the form of %Y-%m-%dT%H:%M:%S
              that indicates when the access token expires

            - refresh_token: this is an optional refresh_token string that can be passed
              if a valid JWT is known. If one is not known, the user will be prompted to
              log into Highwind on the first API call.

            - refresh_token_expires_in: float of number of seconds until the refresh token
              expires

            - refresh_token_expires_at: optional string in the form of %Y-%m-%dT%H:%M:%S
              that indicates when the refresh token expires

        Returns:
            client: The Highwind Client
        """
        if not cls.client_singleton or force_recreate:
            cls.client_singleton = Client(
                access_token=access_token,
                access_token_expires_in=access_token_expires_in,
                access_token_expires_at=access_token_expires_at,
                refresh_token=refresh_token,
                refresh_token_expires_in=refresh_token_expires_in,
                refresh_token_expires_at=refresh_token_expires_at,
            )

        return cls.client_singleton
