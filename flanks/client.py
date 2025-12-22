import os
from datetime import date
from functools import cached_property

from flanks.connect.client import ConnectClient
from flanks.connection import FlanksConnection
from flanks.entities.client import EntitiesClient
from flanks.exceptions import FlanksConfigError


class FlanksClient:
    """Flanks API client with sub-clients for each API domain."""

    _client_id: str
    _client_secret: str

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        *,
        base_url: str = "https://api.flanks.io",
        timeout: float = 60.0,
        retries: int = 1,
        retry_backoff: float = 1.0,
        version: str = "2026-01-01",
    ) -> None:
        resolved_client_id = client_id or os.environ.get("FLANKS_CLIENT_ID")
        resolved_client_secret = client_secret or os.environ.get("FLANKS_CLIENT_SECRET")

        if not resolved_client_id or not resolved_client_secret:
            raise FlanksConfigError(
                "Missing credentials. Provide client_id and client_secret "
                "or set FLANKS_CLIENT_ID and FLANKS_CLIENT_SECRET environment variables."
            )

        self._client_id = resolved_client_id
        self._client_secret = resolved_client_secret

        self._base_url = base_url
        self._timeout = timeout
        self._retries = retries
        self._retry_backoff = retry_backoff
        self._version = date.fromisoformat(version)

    @cached_property
    def transport(self) -> FlanksConnection:
        """Access underlying transport for raw API calls."""
        return FlanksConnection(
            client_id=self._client_id,
            client_secret=self._client_secret,
            base_url=self._base_url,
            timeout=self._timeout,
            retries=self._retries,
            retry_backoff=self._retry_backoff,
        )

    @cached_property
    def entities(self) -> EntitiesClient:
        """Client for Entities API."""
        return EntitiesClient(self.transport)

    @cached_property
    def connect(self) -> ConnectClient:
        """Client for Connect API v2."""
        return ConnectClient(self.transport)

    async def close(self) -> None:
        """Close the client and release resources."""
        if "transport" in self.__dict__:
            await self.transport.close()

    async def __aenter__(self) -> "FlanksClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()
