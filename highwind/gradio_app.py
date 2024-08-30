from typing import Optional

from highwind.client import Client
from highwind.client_factory import ClientFactory


class GradioApp:
    """
    This is a utility class for setting up a Gradio App to work with Highwind.

    Its purpose is to abstract the process of retrieving the Highwind access token from
    the Gradio App's request (https://www.gradio.app/docs/gradio/request). This ensures
    proper authentication and authorization with the Highwind API.

    Example usage:

    ```py
    import gradio as gr
    import highwind

    def communicate_with_highwind(request: gr.Request):
        highwind.GradioApp.setup_with_request(request)
        use_case: highwind.UseCase = highwind.UseCase(id="...")
        use_case.run_inference(...)

    with gr.Blocks() as demo:
        btn.click(
        fn=communicate_with_highwind,
    )

    demo.launch()
    ```
    """

    @classmethod
    def setup_with_request(cls, request) -> Optional[Client]:
        """
        Initialize a Gradio App to work with Highwind. Accepts a gradio.Request object.

        Parameters:
            - request: the gradio.Request object (https://www.gradio.app/docs/gradio/request)

            request needs to have the following keys in the session:
                - access_token (Optional[str])
                - access_token_expires_in (float)
                - access_token_expires_at (Optional[str] in the form of %Y-%m-%dT%H:%M:%S)

                - refresh_token (str)
                - refresh_token_expires_in (float)
                - refresh_token_expires_at (Optional[str] in the form of %Y-%m-%dT%H:%M:%S)

        Returns:
            - An optional highwind.Client instance. This will be None if either the
              request.session is not available (i.e. SessionMiddleware is not used) or
              if the access_token was not present in the request's session.
        """
        try:
            access_token: Optional[str] = request.session.get("access_token", None)
            access_token_expires_in: float = request.session.get(
                "access_token_expires_in", None
            )
            access_token_expires_at: Optional[str] = request.session.get(
                "access_token_expires_at", None
            )

            refresh_token: str = request.session.get("refresh_token", None)
            refresh_token_expires_in: float = request.session.get(
                "refresh_token_expires_in", None
            )
            refresh_token_expires_at: Optional[str] = request.session.get(
                "refresh_token_expires_at", None
            )
        except AssertionError:
            # request.session will raise an AssertionError when SessionMiddleware is not
            # used. This is the case when the Gradio App is not wrapped in a FastAPI
            # application.
            return None

        if not access_token:
            return None

        return ClientFactory.get_client(
            force_recreate=True,
            access_token=access_token,
            access_token_expires_in=access_token_expires_in,
            access_token_expires_at=access_token_expires_at,
            refresh_token=refresh_token,
            refresh_token_expires_in=refresh_token_expires_in,
            refresh_token_expires_at=refresh_token_expires_at,
        )
