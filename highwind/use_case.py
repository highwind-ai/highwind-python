import uuid

from .client import Client


class UseCase:
    """
    Models a UseCase (which is a logical collection of Assets) on Highwind.
    """

    def __init__(self, uuid: uuid.UUID, *args, **kwargs):
        self.client = Client(*args, **kwargs)
        self.uuid: uuid.UUID = uuid
