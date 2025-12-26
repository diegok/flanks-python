from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast, get_args, get_origin, overload

from pydantic import BaseModel

from flanks.connection import FlanksConnection

T = TypeVar("T", bound=BaseModel)


class BaseClient:
    """Base class for all API sub-clients."""

    def __init__(self, transport: FlanksConnection) -> None:
        self.transport = transport

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        model: type[T],
    ) -> T: ...

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        model: type[list[T]],
    ) -> list[T]: ...

    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        model: type[T] | type[list[T]] | None = None,
    ) -> T | list[T] | dict[str, Any] | list[Any]:
        """Execute API call with optional model validation.

        Args:
            path: API endpoint path
            body: JSON body for POST/PUT/DELETE requests
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters for GET requests
            model: Optional Pydantic model to validate response.
                Use `Model` for dict responses, `list[Model]` for list responses.
        """
        result = await self.transport.api_call(path, body, method, params)

        if model is None:
            return result

        if get_origin(model) is list:
            inner_model = get_args(model)[0]
            if not isinstance(result, list):
                raise TypeError(f"Expected list response, got {type(result)}")
            return [inner_model.model_validate(item) for item in result]

        if not isinstance(result, dict):
            raise TypeError(f"Expected dict response, got {type(result)}")
        return cast(type[T], model).model_validate(result)

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
            response = await self.transport.api_call(path, payload)
            if not isinstance(response, dict):
                raise TypeError(f"Expected dict response, got {type(response)}")
            for item in response[item_key]:
                yield model.model_validate(item)
            page_token = response.get("next_page_token")
            if not page_token:
                break
