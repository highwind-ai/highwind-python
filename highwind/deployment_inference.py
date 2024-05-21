from dotenv import load_dotenv

load_dotenv()


import os
from typing import Dict

from .client import Client
from .client_factory import ClientFactory


class DeploymentInference:
    INFERENCE_BASE_URL: str = os.environ.get(
        "INFERENCE_BASE_URL",
        default="https://api.kubeflow.dev.highwind.cloud/v2/models",
    )
    INF_HOST_FQDN: str = os.environ.get(
        "INF_HOST_FQDN",
        default="inf.dev.highwind.cloud",
    )

    def __init__(self, use_case_id: str):
        self.use_case_id: str = use_case_id

        self.client: Client = ClientFactory.client()
        self._raw_data: Dict = self.client.get(
            f"deployments/mine/{self.use_case_id}/deployment/inference"
        )

        self.name: str = self._raw_data["name"]
        self.namespace: str = self._raw_data["namespace"]
        self.inference_url: str = (
            f"{DeploymentInference.INFERENCE_BASE_URL}/{self.name}/infer"
        )

    @property
    def inf_host_header(self) -> str:
        return f"{self.name}.{self.namespace}.{DeploymentInference.INF_HOST_FQDN}"
