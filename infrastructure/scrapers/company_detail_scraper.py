from __future__ import annotations

import json
import base64

from typing import Dict

from infrastructure.http.http_client import RequestsAffinityHttpClient


class DetailFetcher:
    """Fetch and clean detailed company information.

    This class wraps an HTTP client to request a detail endpoint that expects
    a base64-encoded JSON token in the URL.

    Attributes:
        http_client (RequestsAffinityHttpClient): HTTP client used to perform requests.
        endpoint_detail (str): Base URL to which the encoded token will be appended.
        language (str): Language code included in the request payload.
    """

    def __init__(
        self,
        http_client: RequestsAffinityHttpClient,
        endpoint_detail: str,
        language: str,
    ) -> None:
        """Initialize the fetcher with client and endpoint settings.

        Args:
            http_client (RequestsAffinityHttpClient): Configured HTTP client.
            endpoint_detail (str): Detail endpoint base URL (e.g., ".../detail?token=").
            language (str): Language/locale string to include in the payload.

        """
        # Keep a reference to the HTTP client used for all requests
        self.http_client = http_client

        # Save the detail endpoint where the token will be appended
        self.endpoint_detail = endpoint_detail

        # Persist the language so it can be embedded in each request payload
        self.language = language

    def fetch_detail(self, session, cvm_code: str) -> Dict:
        """Fetch the raw detail JSON for a given CVM code.

        Builds a base64-encoded JSON token with the required fields,
        performs the HTTP request, and returns the decoded JSON object.

        Args:
            session: An HTTP session/context passed through to the client.
            cvm_code (str): Company CVM identifier used by the remote API.

        Returns:
            Dict: Parsed JSON payload returned by the detail endpoint.

        Raises:
            Exception: Propagates any network, decoding, or JSON parsing errors
                raised by the underlying HTTP client or standard library.

        """
        # Prepare the request payload with code and language
        payload = {"codeCVM": cvm_code, "language": self.language}

        # Encode the payload as base64 to match the API contract
        token = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

        # Build the final URL by appending the token to the base endpoint
        url = self.endpoint_detail + token

        # Execute the HTTP request using the shared client/session
        body = self.http_client.fetch_with(session, url)

        # Decode the response body and parse it as JSON
        raw = json.loads(body.decode("utf-8"))

        # Return the raw dictionary as obtained from the service
        return raw
