# Flanks Python SDK Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a fully typed, async Python SDK for the Flanks API with automatic authentication handling.

**Architecture:** FlanksClient exposes sub-clients (connect, entities, credentials, etc.) that share a FlanksConnection transport layer. The transport handles OAuth2 token lifecycle, retries, and error mapping. All models use Pydantic with lenient validation.

**Tech Stack:** Python 3.10+, httpx 0.28.1, pydantic 2.12.15, pytest, pytest-asyncio, respx, ruff, mypy

**Design Doc:** `docs/plans/2025-12-21-flanks-python-sdk-design.md`

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `flanks/__init__.py`
- Create: `flanks/_version.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Initialize poetry project**

Run:
```bash
poetry init --name flanks --description "Python SDK for Flanks API" --author "Flanks <dev@flanks.io>" --python "^3.10" --no-interaction
```

**Step 2: Create pyproject.toml with full configuration**

Replace the generated `pyproject.toml` with:

```toml
[tool.poetry]
name = "flanks"
version = "0.1.0"
description = "Python SDK for Flanks API"
authors = ["Flanks <dev@flanks.io>"]
license = "MIT"
readme = "README.md"
repository = "https://github.com/flanksio/flanks-python"
keywords = ["flanks", "api", "sdk", "banking", "aggregation"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
packages = [{ include = "flanks" }]

[tool.poetry.dependencies]
python = "^3.10"
httpx = "^0.28.1"
pydantic = "^2.12.15"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.25"
respx = "^0.22"
ruff = "^0.8"
mypy = "^1.14"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true
```

**Step 3: Create package structure**

```bash
mkdir -p flanks tests
```

**Step 4: Create flanks/_version.py**

```python
__version__ = "0.1.0"
```

**Step 5: Create flanks/__init__.py (minimal)**

```python
from flanks._version import __version__

__all__ = ["__version__"]
```

**Step 6: Create tests/__init__.py**

```python
# Tests package
```

**Step 7: Create tests/conftest.py**

```python
import pytest


@pytest.fixture
def client_id() -> str:
    return "test_client_id"


@pytest.fixture
def client_secret() -> str:
    return "test_client_secret"


@pytest.fixture
def base_url() -> str:
    return "https://api.test.flanks.io"
```

**Step 8: Install dependencies**

Run:
```bash
poetry install
```

**Step 9: Verify setup**

Run:
```bash
poetry run python -c "from flanks import __version__; print(__version__)"
```
Expected: `0.1.0`

**Step 10: Commit**

```bash
git add pyproject.toml poetry.lock flanks/ tests/
git commit -m "chore: initialize project with poetry and dependencies"
```

---

## Task 2: Exceptions Module

**Files:**
- Create: `flanks/exceptions.py`
- Modify: `flanks/__init__.py`
- Create: `tests/test_exceptions.py`

**Step 1: Write failing test for exceptions**

Create `tests/test_exceptions.py`:

```python
from flanks import (
    FlanksError,
    FlanksConfigError,
    FlanksAPIError,
    FlanksAuthError,
    FlanksValidationError,
    FlanksNotFoundError,
    FlanksServerError,
    FlanksNetworkError,
)


class TestExceptionHierarchy:
    def test_flanks_error_is_base(self) -> None:
        error = FlanksError("test")
        assert isinstance(error, Exception)
        assert str(error) == "test"

    def test_config_error_inherits_from_flanks_error(self) -> None:
        error = FlanksConfigError("missing credentials")
        assert isinstance(error, FlanksError)

    def test_api_error_has_status_and_body(self) -> None:
        error = FlanksAPIError(
            "bad request",
            status_code=400,
            response_body={"error": "validation failed"},
        )
        assert isinstance(error, FlanksError)
        assert error.status_code == 400
        assert error.response_body == {"error": "validation failed"}
        assert str(error) == "bad request"

    def test_api_error_optional_fields(self) -> None:
        error = FlanksAPIError("error")
        assert error.status_code is None
        assert error.response_body is None

    def test_auth_error_inherits_from_api_error(self) -> None:
        error = FlanksAuthError("unauthorized", status_code=401)
        assert isinstance(error, FlanksAPIError)
        assert isinstance(error, FlanksError)

    def test_validation_error_inherits_from_api_error(self) -> None:
        error = FlanksValidationError("invalid", status_code=400)
        assert isinstance(error, FlanksAPIError)

    def test_not_found_error_inherits_from_api_error(self) -> None:
        error = FlanksNotFoundError("not found", status_code=404)
        assert isinstance(error, FlanksAPIError)

    def test_server_error_inherits_from_api_error(self) -> None:
        error = FlanksServerError("server error", status_code=500)
        assert isinstance(error, FlanksAPIError)

    def test_network_error_has_cause(self) -> None:
        cause = ConnectionError("connection refused")
        error = FlanksNetworkError("network failure", cause=cause)
        assert isinstance(error, FlanksError)
        assert not isinstance(error, FlanksAPIError)
        assert error.__cause__ is cause

    def test_network_error_optional_cause(self) -> None:
        error = FlanksNetworkError("timeout")
        assert error.__cause__ is None
```

**Step 2: Run test to verify it fails**

Run:
```bash
poetry run pytest tests/test_exceptions.py -v
```
Expected: FAIL with ImportError

**Step 3: Create flanks/exceptions.py**

```python
class FlanksError(Exception):
    """Base exception for all Flanks SDK errors."""

    pass


class FlanksConfigError(FlanksError):
    """Raised when client configuration is invalid."""

    pass


class FlanksAPIError(FlanksError):
    """Base for all API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FlanksAuthError(FlanksAPIError):
    """401/403 - Invalid or expired credentials/token."""

    pass


class FlanksValidationError(FlanksAPIError):
    """400 - Request validation failed."""

    pass


class FlanksNotFoundError(FlanksAPIError):
    """404 - Resource not found."""

    pass


class FlanksServerError(FlanksAPIError):
    """5xx - Server-side error (retryable)."""

    pass


class FlanksNetworkError(FlanksError):
    """Network-level failure (connection refused, timeout, DNS)."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause
```

**Step 4: Update flanks/__init__.py**

```python
from flanks._version import __version__
from flanks.exceptions import (
    FlanksAPIError,
    FlanksAuthError,
    FlanksConfigError,
    FlanksError,
    FlanksNetworkError,
    FlanksNotFoundError,
    FlanksServerError,
    FlanksValidationError,
)

__all__ = [
    "__version__",
    "FlanksError",
    "FlanksConfigError",
    "FlanksAPIError",
    "FlanksAuthError",
    "FlanksValidationError",
    "FlanksNotFoundError",
    "FlanksServerError",
    "FlanksNetworkError",
]
```

**Step 5: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/test_exceptions.py -v
```
Expected: All tests PASS

**Step 6: Run type checking**

Run:
```bash
poetry run mypy flanks/exceptions.py
```
Expected: Success

**Step 7: Commit**

```bash
git add flanks/exceptions.py flanks/__init__.py tests/test_exceptions.py
git commit -m "feat: add exception hierarchy"
```

---

## Task 3: FlanksConnection - Token Management

**Files:**
- Create: `flanks/connection.py`
- Create: `tests/test_connection.py`

**Step 1: Write failing tests for token management**

Create `tests/test_connection.py`:

```python
import time

import httpx
import pytest
import respx

from flanks.connection import FlanksConnection
from flanks.exceptions import FlanksAuthError


class TestFlanksConnectionInit:
    def test_stores_configuration(self) -> None:
        conn = FlanksConnection(
            client_id="test_id",
            client_secret="test_secret",
            base_url="https://api.test.flanks.io",
            timeout=30.0,
            retries=2,
            retry_backoff=0.5,
        )
        assert conn._client_id == "test_id"
        assert conn._client_secret == "test_secret"
        assert conn._base_url == "https://api.test.flanks.io"
        assert conn._timeout == 30.0
        assert conn._retries == 2
        assert conn._retry_backoff == 0.5

    def test_default_values(self) -> None:
        conn = FlanksConnection(client_id="id", client_secret="secret")
        assert conn._base_url == "https://api.flanks.io"
        assert conn._timeout == 60.0
        assert conn._retries == 1
        assert conn._retry_backoff == 1.0

    def test_initial_token_state(self) -> None:
        conn = FlanksConnection(client_id="id", client_secret="secret")
        assert conn._access_token is None
        assert conn._token_expires_at == 0


class TestFlanksConnectionHTTP:
    def test_http_client_lazy_created(self) -> None:
        conn = FlanksConnection(client_id="id", client_secret="secret")
        # Access _http triggers creation
        http = conn._http
        assert isinstance(http, httpx.AsyncClient)
        assert http.base_url == httpx.URL("https://api.flanks.io")
        assert http.timeout == httpx.Timeout(60.0)

    def test_http_client_cached(self) -> None:
        conn = FlanksConnection(client_id="id", client_secret="secret")
        http1 = conn._http
        http2 = conn._http
        assert http1 is http2


class TestTokenRefresh:
    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_success(self) -> None:
        conn = FlanksConnection(
            client_id="test_id",
            client_secret="test_secret",
            base_url="https://api.test.flanks.io",
        )

        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "new_token_123",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
            )
        )

        await conn._refresh_token()

        assert conn._access_token == "new_token_123"
        assert conn._token_expires_at > time.time()
        assert conn._token_expires_at <= time.time() + 3600

    @respx.mock
    @pytest.mark.asyncio
    async def test_refresh_token_invalid_credentials(self) -> None:
        conn = FlanksConnection(
            client_id="bad_id",
            client_secret="bad_secret",
            base_url="https://api.test.flanks.io",
        )

        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(403, json={"error": "access_denied"})
        )

        with pytest.raises(FlanksAuthError) as exc_info:
            await conn._refresh_token()

        assert exc_info.value.status_code == 403


class TestEnsureToken:
    @respx.mock
    @pytest.mark.asyncio
    async def test_refreshes_when_no_token(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )

        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        await conn._ensure_token()
        assert conn._access_token == "token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_refreshes_when_expiring_soon(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "old_token"
        conn._token_expires_at = time.time() + 60  # Expires in 1 minute (< 5 min threshold)

        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "new_token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        await conn._ensure_token()
        assert conn._access_token == "new_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_skips_refresh_when_token_valid(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "valid_token"
        conn._token_expires_at = time.time() + 600  # Expires in 10 minutes

        # No mock - if it tries to refresh, it will fail
        await conn._ensure_token()
        assert conn._access_token == "valid_token"


class TestClose:
    @pytest.mark.asyncio
    async def test_closes_http_client(self) -> None:
        conn = FlanksConnection(client_id="id", client_secret="secret")
        _ = conn._http  # Trigger creation
        await conn.close()
        assert conn._http.is_closed
```

**Step 2: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/test_connection.py -v
```
Expected: FAIL with ImportError

**Step 3: Create flanks/connection.py**

```python
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
```

**Step 4: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/test_connection.py -v
```
Expected: All tests PASS

**Step 5: Run type checking**

Run:
```bash
poetry run mypy flanks/connection.py
```
Expected: Success

**Step 6: Commit**

```bash
git add flanks/connection.py tests/test_connection.py
git commit -m "feat: add FlanksConnection with token management"
```

---

## Task 4: FlanksConnection - API Call with Retries

**Files:**
- Modify: `flanks/connection.py`
- Modify: `tests/test_connection.py`

**Step 1: Add failing tests for api_call**

Append to `tests/test_connection.py`:

```python
class TestAPICall:
    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_post_request(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "valid_token"
        conn._token_expires_at = time.time() + 3600

        respx.post("https://api.test.flanks.io/v0/test/endpoint").mock(
            return_value=httpx.Response(200, json={"result": "success"})
        )

        result = await conn.api_call("/v0/test/endpoint", {"param": "value"})

        assert result == {"result": "success"}
        request = respx.calls.last.request
        assert request.headers["Authorization"] == "Bearer valid_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_get_request(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "valid_token"
        conn._token_expires_at = time.time() + 3600

        respx.get("https://api.test.flanks.io/v0/entities").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )

        result = await conn.api_call("/v0/entities", method="GET")

        assert result == [{"id": 1}]

    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_401_with_token_refresh(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "expired_token"
        conn._token_expires_at = time.time() + 3600  # Looks valid but isn't

        # First call returns 401
        route = respx.post("https://api.test.flanks.io/v0/test")
        route.side_effect = [
            httpx.Response(401, json={"error": "invalid token"}),
            httpx.Response(200, json={"result": "success"}),
        ]

        # Token refresh
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "new_token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        result = await conn.api_call("/v0/test", {"data": "value"})

        assert result == {"result": "success"}
        assert conn._access_token == "new_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_auth_error_after_refresh_fails(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "bad_token"
        conn._token_expires_at = time.time() + 3600

        # Both calls return 401
        respx.post("https://api.test.flanks.io/v0/test").mock(
            return_value=httpx.Response(401, json={"error": "invalid token"})
        )

        # Token refresh succeeds but new token also fails
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "still_bad", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        with pytest.raises(FlanksAuthError):
            await conn.api_call("/v0/test", {"data": "value"})

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_validation_error_on_400(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "token"
        conn._token_expires_at = time.time() + 3600

        respx.post("https://api.test.flanks.io/v0/test").mock(
            return_value=httpx.Response(400, json={"error": "validation failed"})
        )

        with pytest.raises(FlanksValidationError) as exc_info:
            await conn.api_call("/v0/test", {"bad": "data"})

        assert exc_info.value.status_code == 400
        assert exc_info.value.response_body == {"error": "validation failed"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_not_found_error_on_404(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        conn._access_token = "token"
        conn._token_expires_at = time.time() + 3600

        respx.post("https://api.test.flanks.io/v0/test").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )

        with pytest.raises(FlanksNotFoundError) as exc_info:
            await conn.api_call("/v0/test", {"id": "missing"})

        assert exc_info.value.status_code == 404

    @respx.mock
    @pytest.mark.asyncio
    async def test_retries_on_server_error(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
            retries=2,
            retry_backoff=0.01,  # Fast for tests
        )
        conn._access_token = "token"
        conn._token_expires_at = time.time() + 3600

        route = respx.post("https://api.test.flanks.io/v0/test")
        route.side_effect = [
            httpx.Response(500, json={"error": "server error"}),
            httpx.Response(500, json={"error": "server error"}),
            httpx.Response(200, json={"result": "success"}),
        ]

        result = await conn.api_call("/v0/test", {"data": "value"})

        assert result == {"result": "success"}
        assert len(respx.calls) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_raises_server_error_after_retries_exhausted(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
            retries=1,
            retry_backoff=0.01,
        )
        conn._access_token = "token"
        conn._token_expires_at = time.time() + 3600

        respx.post("https://api.test.flanks.io/v0/test").mock(
            return_value=httpx.Response(503, json={"error": "service unavailable"})
        )

        with pytest.raises(FlanksServerError) as exc_info:
            await conn.api_call("/v0/test", {})

        assert exc_info.value.status_code == 503
        assert len(respx.calls) == 2  # Initial + 1 retry

    @respx.mock
    @pytest.mark.asyncio
    async def test_wraps_network_errors(self) -> None:
        conn = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
            retries=0,
        )
        conn._access_token = "token"
        conn._token_expires_at = time.time() + 3600

        respx.post("https://api.test.flanks.io/v0/test").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(FlanksNetworkError) as exc_info:
            await conn.api_call("/v0/test", {})

        assert "Connection refused" in str(exc_info.value)
```

**Step 2: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/test_connection.py::TestAPICall -v
```
Expected: FAIL with AttributeError (api_call not defined)

**Step 3: Add imports and implement api_call**

Update `flanks/connection.py`:

```python
import asyncio
import time
from functools import cached_property

import httpx

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

    async def api_call(
        self,
        path: str,
        body: dict | None = None,
        method: str = "POST",
    ) -> dict | list:
        """Execute API call with automatic auth and retries."""
        await self._ensure_token()

        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                return await self._execute(method, path, body)
            except FlanksServerError as e:
                last_error = e
                if attempt < self._retries:
                    await asyncio.sleep(self._retry_backoff * (2**attempt))
            except FlanksAuthError:
                # Token might have been revoked - refresh and retry once
                await self._refresh_token()
                try:
                    return await self._execute(method, path, body)
                except FlanksAuthError:
                    raise

        if last_error is not None:
            raise last_error

        raise RuntimeError("Unexpected state: no result and no error")

    async def _execute(self, method: str, path: str, body: dict | None) -> dict | list:
        """Execute a single HTTP request."""
        try:
            response = await self._http.request(
                method=method,
                url=path,
                json=body if method != "GET" else None,
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

        return response.json()

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
```

**Step 4: Update test imports**

At the top of `tests/test_connection.py`, update imports:

```python
import time

import httpx
import pytest
import respx

from flanks.connection import FlanksConnection
from flanks.exceptions import (
    FlanksAuthError,
    FlanksNetworkError,
    FlanksNotFoundError,
    FlanksServerError,
    FlanksValidationError,
)
```

**Step 5: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/test_connection.py -v
```
Expected: All tests PASS

**Step 6: Run type checking**

Run:
```bash
poetry run mypy flanks/connection.py
```
Expected: Success

**Step 7: Commit**

```bash
git add flanks/connection.py tests/test_connection.py
git commit -m "feat: add api_call with retries and error handling"
```

---

## Task 5: FlanksClient - Main Client Class

**Files:**
- Create: `flanks/client.py`
- Modify: `flanks/__init__.py`
- Create: `tests/test_client.py`

**Step 1: Write failing tests for FlanksClient**

Create `tests/test_client.py`:

```python
import os
from datetime import date
from unittest.mock import patch

import pytest

from flanks import FlanksClient, FlanksConfigError
from flanks.connection import FlanksConnection


class TestFlanksClientInit:
    def test_accepts_explicit_credentials(self) -> None:
        client = FlanksClient(client_id="test_id", client_secret="test_secret")
        assert client._client_id == "test_id"
        assert client._client_secret == "test_secret"

    def test_reads_credentials_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {"FLANKS_CLIENT_ID": "env_id", "FLANKS_CLIENT_SECRET": "env_secret"},
        ):
            client = FlanksClient()
            assert client._client_id == "env_id"
            assert client._client_secret == "env_secret"

    def test_explicit_credentials_override_env(self) -> None:
        with patch.dict(
            os.environ,
            {"FLANKS_CLIENT_ID": "env_id", "FLANKS_CLIENT_SECRET": "env_secret"},
        ):
            client = FlanksClient(client_id="explicit_id", client_secret="explicit_secret")
            assert client._client_id == "explicit_id"
            assert client._client_secret == "explicit_secret"

    def test_raises_config_error_when_no_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing env vars
            os.environ.pop("FLANKS_CLIENT_ID", None)
            os.environ.pop("FLANKS_CLIENT_SECRET", None)

            with pytest.raises(FlanksConfigError) as exc_info:
                FlanksClient()

            assert "FLANKS_CLIENT_ID" in str(exc_info.value)
            assert "FLANKS_CLIENT_SECRET" in str(exc_info.value)

    def test_raises_config_error_when_partial_credentials(self) -> None:
        with patch.dict(os.environ, {"FLANKS_CLIENT_ID": "only_id"}, clear=True):
            os.environ.pop("FLANKS_CLIENT_SECRET", None)

            with pytest.raises(FlanksConfigError):
                FlanksClient()

    def test_default_configuration(self) -> None:
        client = FlanksClient(client_id="id", client_secret="secret")
        assert client._base_url == "https://api.flanks.io"
        assert client._timeout == 60.0
        assert client._retries == 1
        assert client._retry_backoff == 1.0
        assert client._version == date(2026, 1, 1)

    def test_custom_configuration(self) -> None:
        client = FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.staging.flanks.io",
            timeout=30.0,
            retries=3,
            retry_backoff=0.5,
            version="2025-06-01",
        )
        assert client._base_url == "https://api.staging.flanks.io"
        assert client._timeout == 30.0
        assert client._retries == 3
        assert client._retry_backoff == 0.5
        assert client._version == date(2025, 6, 1)


class TestFlanksClientTransport:
    def test_transport_is_lazily_created(self) -> None:
        client = FlanksClient(client_id="id", client_secret="secret")
        # Transport not yet created
        assert "transport" not in client.__dict__

    def test_transport_returns_flanks_connection(self) -> None:
        client = FlanksClient(client_id="id", client_secret="secret")
        transport = client.transport
        assert isinstance(transport, FlanksConnection)

    def test_transport_is_cached(self) -> None:
        client = FlanksClient(client_id="id", client_secret="secret")
        transport1 = client.transport
        transport2 = client.transport
        assert transport1 is transport2

    def test_transport_uses_client_config(self) -> None:
        client = FlanksClient(
            client_id="my_id",
            client_secret="my_secret",
            base_url="https://custom.api.io",
            timeout=45.0,
            retries=2,
            retry_backoff=2.0,
        )
        transport = client.transport
        assert transport._client_id == "my_id"
        assert transport._client_secret == "my_secret"
        assert transport._base_url == "https://custom.api.io"
        assert transport._timeout == 45.0
        assert transport._retries == 2
        assert transport._retry_backoff == 2.0


class TestFlanksClientContextManager:
    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        async with FlanksClient(client_id="id", client_secret="secret") as client:
            assert isinstance(client, FlanksClient)

    @pytest.mark.asyncio
    async def test_context_manager_closes_transport(self) -> None:
        async with FlanksClient(client_id="id", client_secret="secret") as client:
            _ = client.transport._http  # Force HTTP client creation

        assert client.transport._http.is_closed

    @pytest.mark.asyncio
    async def test_explicit_close(self) -> None:
        client = FlanksClient(client_id="id", client_secret="secret")
        _ = client.transport._http  # Force HTTP client creation
        await client.close()
        assert client.transport._http.is_closed
```

**Step 2: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/test_client.py -v
```
Expected: FAIL with ImportError

**Step 3: Create flanks/client.py**

```python
import os
from datetime import date
from functools import cached_property

from flanks.connection import FlanksConnection
from flanks.exceptions import FlanksConfigError


class FlanksClient:
    """Flanks API client with sub-clients for each API domain."""

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
        self._client_id = client_id or os.environ.get("FLANKS_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("FLANKS_CLIENT_SECRET")

        if not self._client_id or not self._client_secret:
            raise FlanksConfigError(
                "Missing credentials. Provide client_id and client_secret "
                "or set FLANKS_CLIENT_ID and FLANKS_CLIENT_SECRET environment variables."
            )

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
```

**Step 4: Update flanks/__init__.py**

```python
from flanks._version import __version__
from flanks.client import FlanksClient
from flanks.exceptions import (
    FlanksAPIError,
    FlanksAuthError,
    FlanksConfigError,
    FlanksError,
    FlanksNetworkError,
    FlanksNotFoundError,
    FlanksServerError,
    FlanksValidationError,
)

__all__ = [
    "__version__",
    "FlanksClient",
    "FlanksError",
    "FlanksConfigError",
    "FlanksAPIError",
    "FlanksAuthError",
    "FlanksValidationError",
    "FlanksNotFoundError",
    "FlanksServerError",
    "FlanksNetworkError",
]
```

**Step 5: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/test_client.py -v
```
Expected: All tests PASS

**Step 6: Run type checking**

Run:
```bash
poetry run mypy flanks/client.py
```
Expected: Success

**Step 7: Commit**

```bash
git add flanks/client.py flanks/__init__.py tests/test_client.py
git commit -m "feat: add FlanksClient with configuration and transport"
```

---

## Task 6: Base Client & Pagination

**Files:**
- Create: `flanks/base.py`
- Create: `flanks/pagination.py`
- Create: `tests/test_base.py`
- Create: `tests/test_pagination.py`

**Step 1: Write tests for pagination**

Create `tests/test_pagination.py`:

```python
from flanks.pagination import PagedResponse


class TestPagedResponse:
    def test_has_next_when_token_present(self) -> None:
        response: PagedResponse[str] = PagedResponse(
            items=["a", "b", "c"],
            next_page_token="token123",
        )
        assert response.has_next() is True

    def test_has_next_when_token_none(self) -> None:
        response: PagedResponse[str] = PagedResponse(
            items=["a", "b", "c"],
            next_page_token=None,
        )
        assert response.has_next() is False

    def test_items_accessible(self) -> None:
        response: PagedResponse[int] = PagedResponse(
            items=[1, 2, 3],
            next_page_token=None,
        )
        assert response.items == [1, 2, 3]
```

**Step 2: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/test_pagination.py -v
```
Expected: FAIL with ImportError

**Step 3: Create flanks/pagination.py**

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PagedResponse(Generic[T]):
    """Container for paginated API responses."""

    items: list[T]
    next_page_token: str | None

    def has_next(self) -> bool:
        """Check if there are more pages available."""
        return self.next_page_token is not None
```

**Step 4: Run pagination tests**

Run:
```bash
poetry run pytest tests/test_pagination.py -v
```
Expected: All tests PASS

**Step 5: Write tests for base client**

Create `tests/test_base.py`:

```python
import httpx
import pytest
import respx
from pydantic import BaseModel

from flanks.base import BaseClient
from flanks.connection import FlanksConnection


class Item(BaseModel):
    id: int
    name: str


class TestBaseClient:
    def test_stores_transport(self) -> None:
        transport = FlanksConnection(client_id="id", client_secret="secret")
        client = BaseClient(transport)
        assert client._transport is transport


class TestPaginate:
    @respx.mock
    @pytest.mark.asyncio
    async def test_iterates_single_page(self) -> None:
        transport = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        transport._access_token = "token"
        transport._token_expires_at = 9999999999

        respx.post("https://api.test.flanks.io/v0/items").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"id": 1, "name": "one"}, {"id": 2, "name": "two"}],
                    "next_page_token": None,
                },
            )
        )

        client = BaseClient(transport)
        items = [item async for item in client._paginate("/v0/items", {}, "items", Item)]

        assert len(items) == 2
        assert items[0].id == 1
        assert items[1].name == "two"

    @respx.mock
    @pytest.mark.asyncio
    async def test_iterates_multiple_pages(self) -> None:
        transport = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        transport._access_token = "token"
        transport._token_expires_at = 9999999999

        route = respx.post("https://api.test.flanks.io/v0/items")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "items": [{"id": 1, "name": "one"}],
                    "next_page_token": "page2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"id": 2, "name": "two"}],
                    "next_page_token": "page3",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"id": 3, "name": "three"}],
                    "next_page_token": None,
                },
            ),
        ]

        client = BaseClient(transport)
        items = [item async for item in client._paginate("/v0/items", {}, "items", Item)]

        assert len(items) == 3
        assert [item.id for item in items] == [1, 2, 3]
        assert len(respx.calls) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_passes_body_and_page_token(self) -> None:
        transport = FlanksConnection(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        )
        transport._access_token = "token"
        transport._token_expires_at = 9999999999

        route = respx.post("https://api.test.flanks.io/v0/items")
        route.side_effect = [
            httpx.Response(
                200,
                json={"items": [{"id": 1, "name": "one"}], "next_page_token": "page2"},
            ),
            httpx.Response(
                200,
                json={"items": [], "next_page_token": None},
            ),
        ]

        client = BaseClient(transport)
        body = {"filter": "active"}
        _ = [item async for item in client._paginate("/v0/items", body, "items", Item)]

        # Check first request
        first_request = respx.calls[0].request
        import json

        first_body = json.loads(first_request.content)
        assert first_body["filter"] == "active"
        assert first_body["page_token"] is None

        # Check second request includes page token
        second_request = respx.calls[1].request
        second_body = json.loads(second_request.content)
        assert second_body["page_token"] == "page2"
```

**Step 6: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/test_base.py -v
```
Expected: FAIL with ImportError

**Step 7: Create flanks/base.py**

```python
from collections.abc import AsyncIterator
from typing import TypeVar

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
        body: dict,
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
```

**Step 8: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/test_base.py tests/test_pagination.py -v
```
Expected: All tests PASS

**Step 9: Run type checking**

Run:
```bash
poetry run mypy flanks/base.py flanks/pagination.py
```
Expected: Success

**Step 10: Commit**

```bash
git add flanks/base.py flanks/pagination.py tests/test_base.py tests/test_pagination.py
git commit -m "feat: add BaseClient with pagination helper"
```

---

## Task 7: Entities Client (Simple GET Example)

**Files:**
- Create: `flanks/entities/__init__.py`
- Create: `flanks/entities/client.py`
- Create: `flanks/entities/models.py`
- Create: `tests/entities/__init__.py`
- Create: `tests/entities/test_client.py`
- Modify: `flanks/client.py`

**Step 1: Create directory structure**

```bash
mkdir -p flanks/entities tests/entities
touch flanks/entities/__init__.py tests/entities/__init__.py
```

**Step 2: Write tests for entities models**

Create `tests/entities/test_client.py`:

```python
import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.entities.models import Entity


class TestEntity:
    def test_parses_entity(self) -> None:
        entity = Entity.model_validate(
            {
                "id": "bank_123",
                "name": "Test Bank",
                "country": "ES",
                "logo_url": "https://example.com/logo.png",
            }
        )
        assert entity.id == "bank_123"
        assert entity.name == "Test Bank"
        assert entity.country == "ES"
        assert entity.logo_url == "https://example.com/logo.png"

    def test_ignores_extra_fields(self) -> None:
        entity = Entity.model_validate(
            {
                "id": "bank_123",
                "name": "Test Bank",
                "unknown_field": "ignored",
            }
        )
        assert entity.id == "bank_123"
        assert not hasattr(entity, "unknown_field")


class TestEntitiesClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_entities(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.get("https://api.test.flanks.io/v0/bank/available").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "bank_1", "name": "Bank One", "country": "ES"},
                    {"id": "bank_2", "name": "Bank Two", "country": "PT"},
                ],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            entities = await client.entities.list()

        assert len(entities) == 2
        assert entities[0].id == "bank_1"
        assert entities[1].country == "PT"
```

**Step 3: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/entities/test_client.py -v
```
Expected: FAIL with ImportError

**Step 4: Create flanks/entities/models.py**

```python
from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):
    """A banking entity available for connection."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str
    name: str
    country: str | None = None
    logo_url: str | None = None
```

**Step 5: Create flanks/entities/client.py**

```python
from flanks.base import BaseClient
from flanks.entities.models import Entity


class EntitiesClient(BaseClient):
    """Client for Entities API."""

    async def list(self) -> list[Entity]:
        """List all available banking entities."""
        response = await self._transport.api_call("/v0/bank/available", method="GET")
        if not isinstance(response, list):
            raise TypeError(f"Expected list response, got {type(response)}")
        return [Entity.model_validate(item) for item in response]
```

**Step 6: Update flanks/entities/__init__.py**

```python
from flanks.entities.client import EntitiesClient
from flanks.entities.models import Entity

__all__ = ["EntitiesClient", "Entity"]
```

**Step 7: Add entities to FlanksClient**

Update `flanks/client.py`:

```python
import os
from datetime import date
from functools import cached_property

from flanks.connection import FlanksConnection
from flanks.entities.client import EntitiesClient
from flanks.exceptions import FlanksConfigError


class FlanksClient:
    """Flanks API client with sub-clients for each API domain."""

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
        self._client_id = client_id or os.environ.get("FLANKS_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("FLANKS_CLIENT_SECRET")

        if not self._client_id or not self._client_secret:
            raise FlanksConfigError(
                "Missing credentials. Provide client_id and client_secret "
                "or set FLANKS_CLIENT_ID and FLANKS_CLIENT_SECRET environment variables."
            )

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
```

**Step 8: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/entities/test_client.py -v
```
Expected: All tests PASS

**Step 9: Run all tests**

Run:
```bash
poetry run pytest -v
```
Expected: All tests PASS

**Step 10: Commit**

```bash
git add flanks/entities/ flanks/client.py tests/entities/
git commit -m "feat: add Entities client"
```

---

## Task 8: Connect Client (Pagination Example)

**Files:**
- Create: `flanks/connect/__init__.py`
- Create: `flanks/connect/client.py`
- Create: `flanks/connect/models.py`
- Create: `tests/connect/__init__.py`
- Create: `tests/connect/test_client.py`
- Modify: `flanks/client.py`

**Step 1: Create directory structure**

```bash
mkdir -p flanks/connect tests/connect
touch flanks/connect/__init__.py tests/connect/__init__.py
```

**Step 2: Write tests for Connect client**

Create `tests/connect/test_client.py`:

```python
import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.connect.models import (
    Connector,
    Session,
    SessionConfig,
    SessionQuery,
    SessionStatus,
)
from flanks.pagination import PagedResponse


class TestSessionModel:
    def test_parses_session(self) -> None:
        session = Session.model_validate(
            {
                "session_id": "sess_123",
                "status": "Waiting:ProvideCredentials",
                "connection_id": "conn_456",
            }
        )
        assert session.session_id == "sess_123"
        assert session.status == SessionStatus.WAITING_CREDENTIALS
        assert session.connection_id == "conn_456"

    def test_optional_fields(self) -> None:
        session = Session.model_validate(
            {
                "session_id": "sess_123",
                "status": "Finished:OK",
            }
        )
        assert session.connection_id is None
        assert session.error_code is None


class TestConnectClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_sessions_iterator(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        route = respx.post("https://api.test.flanks.io/connect/v2/sessions/list-sessions")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "items": [{"session_id": "s1", "status": "Finished:OK"}],
                    "next_page_token": "page2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"session_id": "s2", "status": "Finished:Error"}],
                    "next_page_token": None,
                },
            ),
        ]

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            sessions = [s async for s in client.connect.list_sessions()]

        assert len(sessions) == 2
        assert sessions[0].session_id == "s1"
        assert sessions[1].status == SessionStatus.FINISHED_ERROR

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_sessions_with_query(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/sessions/list-sessions").mock(
            return_value=httpx.Response(
                200,
                json={"items": [{"session_id": "s1", "status": "Finished:OK"}], "next_page_token": None},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            query = SessionQuery(status_in=[SessionStatus.FINISHED_OK])
            sessions = [s async for s in client.connect.list_sessions(query)]

        assert len(sessions) == 1
        # Verify query was sent
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["query"]["status_in"] == ["Finished:OK"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_sessions_page(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/sessions/list-sessions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"session_id": "s1", "status": "Finished:OK"}],
                    "next_page_token": "next_token",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            page = await client.connect.list_sessions_page()

        assert isinstance(page, PagedResponse)
        assert len(page.items) == 1
        assert page.next_page_token == "next_token"
        assert page.has_next()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/sessions/create-session").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session": {
                        "session_id": "new_sess",
                        "status": "Waiting:ProvideCredentials",
                    }
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            config = SessionConfig(connector_id="conn_123")
            session = await client.connect.create_session(config)

        assert session.session_id == "new_sess"
        assert session.status == SessionStatus.WAITING_CREDENTIALS

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_connectors(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/connect/v2/connectors/list-connectors").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"connector_id": "c1", "name": "Bank One"}],
                    "next_page_token": None,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            connectors = [c async for c in client.connect.list_connectors()]

        assert len(connectors) == 1
        assert connectors[0].connector_id == "c1"
```

**Step 3: Run tests to verify they fail**

Run:
```bash
poetry run pytest tests/connect/test_client.py -v
```
Expected: FAIL with ImportError

**Step 4: Create flanks/connect/models.py**

```python
from enum import Enum

from pydantic import BaseModel, ConfigDict


class SessionStatus(str, Enum):
    WAITING_CREDENTIALS = "Waiting:ProvideCredentials"
    WAITING_CHALLENGE = "Waiting:Challenge"
    PROCESSING_CREDENTIALS = "Processing:ProvideCredentials"
    PROCESSING_CHALLENGE = "Processing:Challenge"
    FINISHED_OK = "Finished:OK"
    FINISHED_ERROR = "Finished:Error"


class SessionErrorCode(str, Enum):
    INVALID_CREDENTIALS = "InvalidCredentials"
    INVALID_CHALLENGE = "InvalidChallengeResponse"
    UNSUPPORTED_CHALLENGE = "UnsupportedChallengeMethod"
    USER_INTERACTION_NEEDED = "UserInteractionNeeded"
    INTERNAL_ERROR = "InternalError"


class Session(BaseModel):
    """A connection session."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    session_id: str
    status: SessionStatus
    connection_id: str | None = None
    error_code: SessionErrorCode | None = None


class SessionQuery(BaseModel):
    """Query parameters for listing sessions."""

    model_config = ConfigDict(extra="ignore")

    session_id_in: list[str] | None = None
    status_in: list[SessionStatus] | None = None
    connection_id_in: list[str] | None = None
    error_code_in: list[SessionErrorCode] | None = None


class SessionConfig(BaseModel):
    """Configuration for creating a session."""

    model_config = ConfigDict(extra="ignore")

    connector_id: str


class Connector(BaseModel):
    """A banking connector."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    connector_id: str
    name: str
```

**Step 5: Create flanks/connect/client.py**

```python
from collections.abc import AsyncIterator

from flanks.base import BaseClient
from flanks.connect.models import Connector, Session, SessionConfig, SessionQuery
from flanks.pagination import PagedResponse


class ConnectClient(BaseClient):
    """Client for Connect API v2."""

    async def list_sessions(
        self,
        query: SessionQuery | None = None,
    ) -> AsyncIterator[Session]:
        """Iterate over all sessions matching query."""
        async for session in self._paginate(
            "/connect/v2/sessions/list-sessions",
            {"query": query.model_dump(exclude_none=True) if query else {}},
            "items",
            Session,
        ):
            yield session

    async def list_sessions_page(
        self,
        query: SessionQuery | None = None,
        page_token: str | None = None,
    ) -> PagedResponse[Session]:
        """Fetch a single page of sessions."""
        response = await self._transport.api_call(
            "/connect/v2/sessions/list-sessions",
            {
                "query": query.model_dump(exclude_none=True) if query else {},
                "page_token": page_token,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return PagedResponse(
            items=[Session.model_validate(item) for item in response["items"]],
            next_page_token=response.get("next_page_token"),
        )

    async def create_session(self, config: SessionConfig) -> Session:
        """Create a new connection session."""
        response = await self._transport.api_call(
            "/connect/v2/sessions/create-session",
            {"configuration": config.model_dump()},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return Session.model_validate(response["session"])

    async def list_connectors(
        self,
        connector_ids: list[str] | None = None,
    ) -> AsyncIterator[Connector]:
        """Iterate over available connectors."""
        query = {"connector_id_in": connector_ids} if connector_ids else {}
        async for connector in self._paginate(
            "/connect/v2/connectors/list-connectors",
            {"query": query},
            "items",
            Connector,
        ):
            yield connector
```

**Step 6: Update flanks/connect/__init__.py**

```python
from flanks.connect.client import ConnectClient
from flanks.connect.models import (
    Connector,
    Session,
    SessionConfig,
    SessionErrorCode,
    SessionQuery,
    SessionStatus,
)

__all__ = [
    "ConnectClient",
    "Connector",
    "Session",
    "SessionConfig",
    "SessionErrorCode",
    "SessionQuery",
    "SessionStatus",
]
```

**Step 7: Add connect to FlanksClient**

Update `flanks/client.py` to add the connect property:

```python
import os
from datetime import date
from functools import cached_property

from flanks.connect.client import ConnectClient
from flanks.connection import FlanksConnection
from flanks.entities.client import EntitiesClient
from flanks.exceptions import FlanksConfigError


class FlanksClient:
    """Flanks API client with sub-clients for each API domain."""

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
        self._client_id = client_id or os.environ.get("FLANKS_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("FLANKS_CLIENT_SECRET")

        if not self._client_id or not self._client_secret:
            raise FlanksConfigError(
                "Missing credentials. Provide client_id and client_secret "
                "or set FLANKS_CLIENT_ID and FLANKS_CLIENT_SECRET environment variables."
            )

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
    def connect(self) -> ConnectClient:
        """Client for Connect API v2."""
        return ConnectClient(self.transport)

    @cached_property
    def entities(self) -> EntitiesClient:
        """Client for Entities API."""
        return EntitiesClient(self.transport)

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
```

**Step 8: Run tests to verify they pass**

Run:
```bash
poetry run pytest tests/connect/test_client.py -v
```
Expected: All tests PASS

**Step 9: Run all tests**

Run:
```bash
poetry run pytest -v
```
Expected: All tests PASS

**Step 10: Commit**

```bash
git add flanks/connect/ flanks/client.py tests/connect/
git commit -m "feat: add Connect client with sessions and connectors"
```

---

## Task 9: Credentials Client

**Files:**
- Create: `flanks/credentials/__init__.py`
- Create: `flanks/credentials/client.py`
- Create: `flanks/credentials/models.py`
- Create: `tests/credentials/__init__.py`
- Create: `tests/credentials/test_client.py`
- Modify: `flanks/client.py`

This follows the same pattern as Task 7 and 8. The Credentials API has these endpoints:

- `get_status(credentials_token)` → POST /v0/bank/credentials/status
- `list(page)` → POST /v0/bank/credentials/list (page-number pagination)
- `force_sca(credentials_token)` → PUT /v0/bank/credentials/status
- `force_reset(credentials_token)` → PUT /v0/bank/credentials/status
- `force_transaction(credentials_token)` → PUT /v0/bank/credentials/status
- `delete(credentials_token)` → DELETE /v0/bank/credentials

Implementation follows the same TDD pattern. See design doc for full endpoint details.

**Commit message:** `feat: add Credentials client`

---

## Task 10: Aggregation v1 Client

**Files:**
- Create: `flanks/aggregation_v1/__init__.py`
- Create: `flanks/aggregation_v1/client.py`
- Create: `flanks/aggregation_v1/models.py`
- Create: `tests/aggregation_v1/__init__.py`
- Create: `tests/aggregation_v1/test_client.py`
- Modify: `flanks/client.py`

Endpoints to implement:

- `get_portfolios(credentials_token, query)` → POST /v0/bank/credentials/portfolio
- `get_investments(credentials_token, query)` → POST /v0/bank/credentials/investment
- `get_investment_transactions(credentials_token, query)` → POST /v0/bank/credentials/investment/transaction
- `get_accounts(credentials_token, query)` → POST /v0/bank/credentials/account
- `get_account_transactions(credentials_token, query)` → POST /v0/bank/credentials/data
- `get_liabilities(credentials_token, query)` → POST /v0/bank/credentials/liability
- `get_liability_transactions(credentials_token, query)` → POST /v0/bank/credentials/liability/transaction
- `get_cards(credentials_token, query)` → POST /v0/bank/credentials/card
- `get_card_transactions(credentials_token, query)` → POST /v0/bank/credentials/card/transaction
- `get_identity(credentials_token)` → POST /v0/bank/credentials/auth/
- `get_holders(credentials_token)` → POST /v0/bank/credentials/holder

**Commit message:** `feat: add Aggregation v1 client`

---

## Task 11: Aggregation v2 Client

**Files:**
- Create: `flanks/aggregation_v2/__init__.py`
- Create: `flanks/aggregation_v2/client.py`
- Create: `flanks/aggregation_v2/models.py`
- Create: `tests/aggregation_v2/__init__.py`
- Create: `tests/aggregation_v2/test_client.py`
- Modify: `flanks/client.py`

Endpoints to implement:

- `list_products(query)` → POST /aggregation/v2/list-products (paginated)
- `set_product_labels(product_id, labels)` → POST /aggregation/v2/set-product-labels
- `list_transactions(query)` → POST /aggregation/v2/list-transactions (paginated)
- `set_transaction_labels(transaction_id, labels)` → POST /aggregation/v2/set-transaction-labels

Also add the `aggregation` property that returns v1 or v2 based on version.

**Commit message:** `feat: add Aggregation v2 client with version-based selection`

---

## Task 12: Links Client

**Files:**
- Create: `flanks/links/__init__.py`
- Create: `flanks/links/client.py`
- Create: `flanks/links/models.py`
- Create: `tests/links/__init__.py`
- Create: `tests/links/test_client.py`
- Modify: `flanks/client.py`

Endpoints to implement:

- `list()` → GET /v0/links/list-links
- `create(redirect_uri, name, ...)` → POST /v0/links/create-link
- `edit(token, ...)` → POST /v0/links/edit-link
- `delete(token)` → POST /v0/links/delete-link
- `pause(token)` → POST /v0/links/pause-link
- `resume(token)` → POST /v0/links/resume-link
- `get_unused_codes(link_token)` → GET /v0/platform/link
- `exchange_code(code)` → POST /v0/platform/link

**Commit message:** `feat: add Links client (legacy)`

---

## Task 13: Report Client

**Files:**
- Create: `flanks/report/__init__.py`
- Create: `flanks/report/client.py`
- Create: `flanks/report/models.py`
- Create: `tests/report/__init__.py`
- Create: `tests/report/test_client.py`
- Modify: `flanks/client.py`

Endpoints to implement:

- `list_templates()` → GET /report/v1/list-templates
- `build_report(template_id, language, start_date, end_date, ...)` → POST /report/v1/build-report
- `get_status(report_id)` → POST /report/v1/get-report-status
- `get_content_url(report_id)` → POST /report/v1/get-report-content

**Commit message:** `feat: add Report client (beta)`

---

## Task 14: Final Exports & README

**Files:**
- Modify: `flanks/__init__.py` - export all models
- Create: `README.md`

**Step 1: Update flanks/__init__.py with all exports**

Export key models from each sub-module for convenient access.

**Step 2: Create README.md**

```markdown
# Flanks Python SDK

Async Python SDK for the [Flanks API](https://docs.flanks.io/).

## Installation

```bash
pip install flanks
```

## Quick Start

```python
import asyncio
from flanks import FlanksClient

async def main():
    async with FlanksClient() as flanks:
        # Uses FLANKS_CLIENT_ID and FLANKS_CLIENT_SECRET env vars

        # List banking entities
        entities = await flanks.entities.list()

        # Iterate sessions
        async for session in flanks.connect.list_sessions():
            print(session.session_id, session.status)

        # Aggregation (v2 by default)
        async for product in flanks.aggregation.list_products():
            print(product)

asyncio.run(main())
```

## Configuration

```python
client = FlanksClient(
    client_id="your_client_id",      # or FLANKS_CLIENT_ID env var
    client_secret="your_secret",      # or FLANKS_CLIENT_SECRET env var
    base_url="https://api.flanks.io", # optional
    timeout=60.0,                     # request timeout in seconds
    retries=1,                        # retry count for server errors
    version="2026-01-01",             # API version date
)
```

## License

MIT
```

**Step 3: Commit**

```bash
git add flanks/__init__.py README.md
git commit -m "docs: add README and finalize exports"
```

---

## Task 15: Type Checking & Linting

**Step 1: Run mypy on entire package**

```bash
poetry run mypy flanks/
```

Fix any type errors.

**Step 2: Run ruff**

```bash
poetry run ruff check flanks/ tests/
poetry run ruff format flanks/ tests/
```

**Step 3: Commit fixes**

```bash
git add -A
git commit -m "chore: fix type and lint errors"
```

---

## Task 16: Final Test Run

**Step 1: Run all tests with coverage**

```bash
poetry run pytest -v --tb=short
```

Expected: All tests PASS

**Step 2: Verify package builds**

```bash
poetry build
```

Expected: Creates `dist/flanks-0.1.0.tar.gz` and `dist/flanks-0.1.0-py3-none-any.whl`

**Step 3: Final commit and tag**

```bash
git add -A
git commit -m "chore: prepare v0.1.0 release"
git tag v0.1.0
```

---

Plan complete and saved to `docs/plans/2025-12-21-flanks-sdk-implementation.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
