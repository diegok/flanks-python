from __future__ import annotations

import asyncio
import time
from functools import cached_property
from typing import Any, TypeVar, cast, get_args, get_origin, overload

import httpx
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

from flanks.exceptions import (
    FlanksAuthError,
    FlanksNetworkError,
    FlanksNotFoundError,
    FlanksServerError,
    FlanksValidationError,
)


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

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        response_model: type[T],
    ) -> T: ...

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        response_model: type[list[T]],
    ) -> list[T]: ...

    @overload
    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]: ...

    async def api_call(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        *,
        response_model: type[T] | type[list[T]] | None = None,
    ) -> T | list[T] | dict[str, Any] | list[Any]:
        """Execute API call with automatic auth and retries.

        Args:
            path: API endpoint path
            body: JSON body for POST/PUT/DELETE requests
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters for GET requests
            response_model: Optional Pydantic model to validate response.
                Use `Model` for dict responses, `list[Model]` for list responses.
        """
        await self._ensure_token()

        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                result = await self._execute(method, path, body, params)
                return self._validate_response(result, response_model)
            except FlanksServerError as e:
                last_error = e
                if attempt < self._retries:
                    await asyncio.sleep(self._retry_backoff * (2**attempt))
            except FlanksAuthError:
                # Token might have been revoked - refresh and retry once
                await self._refresh_token()
                try:
                    result = await self._execute(method, path, body, params)
                    return self._validate_response(result, response_model)
                except FlanksAuthError:
                    raise

        if last_error is not None:
            raise last_error

        raise RuntimeError("Unexpected state: no result and no error")

    def _validate_response(
        self,
        result: dict[str, Any] | list[Any],
        response_model: type[T] | type[list[T]] | None,
    ) -> T | list[T] | dict[str, Any] | list[Any]:
        """Validate and convert response to model if specified."""
        if response_model is None:
            return result

        if get_origin(response_model) is list:
            inner_model = get_args(response_model)[0]
            if not isinstance(result, list):
                raise TypeError(f"Expected list response, got {type(result)}")
            return [inner_model.model_validate(item) for item in result]

        if not isinstance(result, dict):
            raise TypeError(f"Expected dict response, got {type(result)}")
        return cast(type[T], response_model).model_validate(result)

    async def _execute(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Execute a single HTTP request."""
        try:
            response = await self._http.request(
                method=method,
                url=path,
                json=body if method != "GET" else None,
                params=params,
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
        except httpx.HTTPError as e:
            raise FlanksNetworkError(str(e), cause=e) from e

        if response.status_code == 401:
            raise FlanksAuthError(
                "Invalid or expired token",
                status_code=401,
                response_body=response.json(),
            )
        if response.status_code == 400:
            raise FlanksValidationError(
                "Validation error",
                status_code=400,
                response_body=response.json(),
            )
        if response.status_code == 404:
            raise FlanksNotFoundError(
                "Resource not found",
                status_code=404,
                response_body=response.json(),
            )
        if response.status_code >= 500:
            raise FlanksServerError(
                "Server error",
                status_code=response.status_code,
                response_body=response.json(),
            )

        result: dict[str, Any] | list[Any] = response.json()
        return result
