import time
from functools import cached_property

import httpx

from flanks.exceptions import FlanksAuthError


class FlanksConnection:
    """Internal HTTP transport handling auth and requests."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.flanks.io",
        timeout: float = 60.0,
        retries: int = 1,
        retry_backoff: float = 1.0,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url
        self._timeout = timeout
        self._retries = retries
        self._retry_backoff = retry_backoff

        self._access_token: str | None = None
        self._token_expires_at: float = 0

    @cached_property
    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        )

    async def _refresh_token(self) -> None:
        """Fetch new access token via client credentials flow."""
        response = await self._http.post(
            "/v0/token",
            json={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
        )

        if response.status_code == 403:
            raise FlanksAuthError(
                "Invalid client credentials",
                status_code=403,
                response_body=response.json(),
            )

        response.raise_for_status()

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]

    async def _ensure_token(self) -> None:
        """Proactive refresh if token expires within 5 minutes."""
        if time.time() > self._token_expires_at - 300:
            await self._refresh_token()

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._http.aclose()
