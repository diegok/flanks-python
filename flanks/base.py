from collections.abc import AsyncIterator
from typing import Any, TypeVar

from pydantic import BaseModel

from flanks.connection import FlanksConnection

T = TypeVar("T", bound=BaseModel)


class BaseClient:
    """Base class for all API sub-clients."""

    def __init__(self, transport: FlanksConnection) -> None:
        self._transport = transport

    async def _paginate(
        self,
        path: str,
        body: dict[str, Any],
        item_key: str,
        model: type[T],
    ) -> AsyncIterator[T]:
        """Generic pagination helper for list endpoints."""
        page_token: str | None = None
        while True:
            payload = {**body, "page_token": page_token}
            response = await self._transport.api_call(path, payload)
            if not isinstance(response, dict):
                raise TypeError(f"Expected dict response, got {type(response)}")
            for item in response[item_key]:
                yield model.model_validate(item)
            page_token = response.get("next_page_token")
            if not page_token:
                break
