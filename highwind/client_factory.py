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
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expiry: Optional[str] = None,
    ) -> Client:
        """
        Gets the existing Highwind Client if present, or creates one.

        Parameters:
            - access_token: this is an optional access_token string that can be passed
              if a valid JWT is known. If one is not known, the user will be prompted to
              log into Highwind on the first API call.

            - refresh_token: this is an optional refresh_token string

            - token_expiry: this is an optional token_expiry string in the form of
              %Y-%m-%dT%H:%M:%S

        Returns:
            client: The Highwind Client
        """
        if cls.client_singleton:
            return cls.client_singleton
        else:
            cls.client_singleton = Client(
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
            return cls.client_singleton
