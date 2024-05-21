from typing import Optional

from .client import Client


class ClientFactory:
    """
    Factory to return a singleton instance of a Client
    """

    client_singleton: Optional[Client] = None

    @classmethod
    def client(cls) -> Client:
        if cls.client_singleton:
            return cls.client_singleton
        else:
            cls.client_singleton = Client()
            return cls.client_singleton
