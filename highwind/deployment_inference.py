from typing import Dict

from .client import Client
from .client_factory import ClientFactory


class DeploymentInference:
    def __init__(self, use_case_id: str):
        self.use_case_id: str = use_case_id

        self.client: Client = ClientFactory.client()
        self._raw_data: Dict = self.client.get(
            f"deployments/mine/{self.use_case_id}/deployment/inference"
        )

        self.inference_url: str = self._raw_data["inference_url"]
