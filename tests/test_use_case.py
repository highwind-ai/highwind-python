import json
from typing import Optional

from highwind import DeploymentInference, UseCase


class TestUseCase:
    def test_on_initialization_sets_details_based_on_api_return_value(self, mock_api):
        use_case_id: str = "d84258c7-b531-4ee8-8aca-639658c189c8"

        with open("tests/fixtures/use_case.json") as fixture:
            mock_use_case = json.load(fixture)

        mock_api.get(
            f"https://api.dev.highwind.cloud/api/v1/use_cases/mine/{use_case_id}/",
            json=mock_use_case,
        )

        use_case: UseCase = UseCase(id=use_case_id)

        assert use_case.name == "iris-classifier"
        assert use_case.description == "iris-classifier description..."

    def test_can_run_inference_on_a_deployed_use_case(self, mock_api):
        use_case_id: str = "d84258c7-b531-4ee8-8aca-639658c189c8"

        with open("tests/fixtures/deployed_use_case.json") as fixture:
            mock_use_case = json.load(fixture)

        mock_api.get(
            f"https://api.dev.highwind.cloud/api/v1/use_cases/mine/{use_case_id}/",
            json=mock_use_case,
        )

        with open("tests/fixtures/deployment_inference.json") as fixture:
            mock_deployment_inference = json.load(fixture)

        mock_api.get(
            f"https://api.dev.highwind.cloud/api/v1/deployments/mine/{use_case_id}/deployment/inference/",
            json=mock_deployment_inference,
        )

        use_case: UseCase = UseCase(id=use_case_id)

        assert use_case.name == "iris-classifier"
        assert use_case.description == "iris-classifier description..."

        deployment_inference: Optional[DeploymentInference] = (
            use_case.deployment_inference
        )

        assert deployment_inference is not None

        assert (
            deployment_inference.inference_url
            == "http://abcd1234.efgh5678.inf.dev.highwind.cloud"
        )

        mock_inference_response = {"some": "response"}

        mock_api.post(
            "http://abcd1234.efgh5678.inf.dev.highwind.cloud/",
            json=mock_inference_response,
        )

        use_case.run_inference(inference_payload={})
