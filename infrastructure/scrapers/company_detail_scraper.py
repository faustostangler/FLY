from __future__ import annotations

import json
import base64

from typing import Dict

from infrastructure.http.http_client import RequestsAffinityHttpClient

class DetailFetcher:
    """Fetch and clean detailed company information using an HTTP client."""

    def __init__(
        self,
        http_client: RequestsAffinityHttpClient,
        endpoint_detail: str,
        language: str,
    ) -> None:
        """Store HTTP client and configuration."""
        self.http_client = http_client
        self.endpoint_detail = endpoint_detail
        self.language = language

    def fetch_detail(self, session, cvm_code: str) -> Dict:
        """Fetch detail JSON and return the raw dict."""
        payload = {"codeCVM": cvm_code, "language": self.language}
        token = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

        url = self.endpoint_detail + token
        body = self.http_client.fetch_with(session, url)
        raw = json.loads(body.decode("utf-8"))

        return raw

