from typing import Dict, Optional

import requests

from .client import Client
from .client_factory import ClientFactory
from .deployment_inference import DeploymentInference


class UseCase:
    """
    Models a UseCase (which is a logical collection of Assets) on Highwind.
    """

    def __init__(self, id: str):
        self.id: str = id

        self.client: Client = ClientFactory.client()
        self._raw_data: Dict = self.client.get(f"use_cases/mine/{self.id}")

        self._extract_basic_details()
        self._extract_deployment_details()

    def run_inference(self, inference_payload: Dict) -> Dict:
        if self.deployment_inference:
            headers: Dict = {
                "Authorization": self.client.access_token,
                "infHost": self.deployment_inference.inf_host_header,
            }

            response = requests.post(
                url=self.deployment_inference.inference_url,
                json=inference_payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    def _extract_basic_details(self) -> None:
        self.name: str = self._raw_data["name"]
        self.description: str = self._raw_data["description"]

    def _extract_deployment_details(self) -> None:
        self.deployment_id: str = self._raw_data.get("deployment_details", {}).get(
            "deployment_id"
        )

        self.deployment_inference: Optional[DeploymentInference] = None

        if self.deployment_id:
            self.deployment_inference = DeploymentInference(use_case_id=self.id)

    def __str__(self) -> str:
        return f"{self.name} (UseCase)"

    def __repr__(self) -> str:
        return str(self)
