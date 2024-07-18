from typing import Optional

from .client import Client


class ClientFactory:
    """
    Factory to return a singleton instance of a Client
    """

    client_singleton: Optional[Client] = None

    @classmethod
    def get_client(cls, access_token: Optional[str] = None) -> Client:
        """
        Gets the existing Highwind Client if present, or creates one.

        Parameters:
            - access_token: this is an optional access_token string that can be passed
              if a valid JWT is known. If one is not known, the user will be prompted to
              log into Highwind on the first API call.

        Returns:
            client: The Highwind Client
        """
        if cls.client_singleton:
            return cls.client_singleton
        else:
            cls.client_singleton = Client(access_token=access_token)
            return cls.client_singleton
