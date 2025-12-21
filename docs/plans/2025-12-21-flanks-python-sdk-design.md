# Flanks Python SDK Design

## Overview

A fully typed, async Python SDK for the Flanks API using httpx and Pydantic.

## Package Info

- **Package name**: `flanks` (PyPI)
- **Python version**: 3.10+
- **Dependencies**:
  - `httpx ^0.28.1`
  - `pydantic ^2.12.15`

## Architecture

```
FlanksClient (public interface)
├── transport: FlanksConnection (HTTP core, lazy-initialized)
│   ├── handles OAuth2 client credentials flow
│   ├── proactive token refresh (5 min before expiry)
│   ├── reactive token refresh (on 401, retry once)
│   ├── api_call(path, body=None, method="POST") → dict
│   └── retries with exponential backoff
│
├── connect: ConnectClient
├── entities: EntitiesClient
├── credentials: CredentialsClient
├── aggregation: → v1 or v2 based on version parameter
├── aggregation_v1: AggregationV1Client
├── aggregation_v2: AggregationV2Client
├── links: LinksClient
└── report: ReportClient
```

## Package Structure

```
flanks/
├── __init__.py              # Exports FlanksClient, exceptions
├── client.py                # FlanksClient main class
├── connection.py            # FlanksConnection (HTTP core)
├── exceptions.py            # All exception types
├── base.py                  # BaseClient for sub-clients
├── pagination.py            # PagedResponse helper
├── _version.py              # Version info
│
├── connect/
│   ├── __init__.py
│   ├── client.py            # ConnectClient
│   └── models.py            # Session, Connector, etc.
│
├── entities/
│   ├── __init__.py
│   ├── client.py            # EntitiesClient
│   └── models.py            # Entity
│
├── credentials/
│   ├── __init__.py
│   ├── client.py            # CredentialsClient
│   └── models.py            # CredentialStatus, etc.
│
├── aggregation_v1/
│   ├── __init__.py
│   ├── client.py            # AggregationV1Client
│   └── models.py            # Portfolio, Account, etc.
│
├── aggregation_v2/
│   ├── __init__.py
│   ├── client.py            # AggregationV2Client
│   └── models.py            # Product, Transaction, etc.
│
├── links/
│   ├── __init__.py
│   ├── client.py            # LinksClient
│   └── models.py            # Link, LinkCode
│
└── report/
    ├── __init__.py
    ├── client.py            # ReportClient
    └── models.py            # ReportTemplate, Report
```

## FlanksClient

```python
import os
from datetime import date
from functools import cached_property

class FlanksClient:
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
        return ConnectClient(self.transport)

    @cached_property
    def entities(self) -> EntitiesClient:
        return EntitiesClient(self.transport)

    @cached_property
    def credentials(self) -> CredentialsClient:
        return CredentialsClient(self.transport)

    @cached_property
    def aggregation_v1(self) -> AggregationV1Client:
        return AggregationV1Client(self.transport)

    @cached_property
    def aggregation_v2(self) -> AggregationV2Client:
        return AggregationV2Client(self.transport)

    @property
    def aggregation(self) -> AggregationV1Client | AggregationV2Client:
        if self._version >= date(2026, 1, 1):
            return self.aggregation_v2
        return self.aggregation_v1

    @cached_property
    def links(self) -> LinksClient:
        return LinksClient(self.transport)

    @cached_property
    def report(self) -> ReportClient:
        return ReportClient(self.transport)

    async def close(self) -> None:
        await self.transport.close()

    async def __aenter__(self) -> "FlanksClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
```

## FlanksConnection

```python
import asyncio
import time
from functools import cached_property
import httpx

class FlanksConnection:
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
    ) -> dict:
        await self._ensure_token()

        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                return await self._execute(method, path, body)
            except FlanksServerError as e:
                last_error = e
                if attempt < self._retries:
                    await asyncio.sleep(self._retry_backoff * (2 ** attempt))
            except FlanksAuthError:
                await self._refresh_token()
                try:
                    return await self._execute(method, path, body)
                except FlanksAuthError:
                    raise

        raise last_error

    async def _ensure_token(self) -> None:
        if time.time() > self._token_expires_at - 300:
            await self._refresh_token()

    async def _refresh_token(self) -> None:
        response = await self._http.post(
            "/v0/token",
            json={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials",
            },
        )
        if response.status_code == 403:
            raise FlanksAuthError("Invalid client credentials", status_code=403)
        response.raise_for_status()

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]

    async def _execute(self, method: str, path: str, body: dict | None) -> dict:
        response = await self._http.request(
            method=method,
            url=path,
            json=body,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )

        if response.status_code == 401:
            raise FlanksAuthError("Invalid or expired token", status_code=401, response_body=response.json())
        if response.status_code == 400:
            raise FlanksValidationError("Validation error", status_code=400, response_body=response.json())
        if response.status_code == 404:
            raise FlanksNotFoundError("Resource not found", status_code=404, response_body=response.json())
        if response.status_code >= 500:
            raise FlanksServerError("Server error", status_code=response.status_code, response_body=response.json())

        return response.json()

    async def close(self) -> None:
        await self._http.aclose()
```

## Exceptions

```python
class FlanksError(Exception):
    """Base exception for all Flanks SDK errors."""
    pass


class FlanksConfigError(FlanksError):
    """Raised when client configuration is invalid."""
    pass


class FlanksAPIError(FlanksError):
    """Base for all API-related errors."""

    def __init__(self, message: str, status_code: int | None = None, response_body: dict | None = None):
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

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.__cause__ = cause
```

## BaseClient & Pagination

```python
# flanks/base.py

from collections.abc import AsyncIterator
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseClient:
    def __init__(self, transport: FlanksConnection) -> None:
        self._transport = transport

    async def _paginate(
        self,
        path: str,
        body: dict,
        item_key: str,
        model: type[T],
    ) -> AsyncIterator[T]:
        page_token: str | None = None
        while True:
            payload = {**body, "page_token": page_token}
            response = await self._transport.api_call(path, payload)
            for item in response[item_key]:
                yield model.model_validate(item)
            page_token = response.get("next_page_token")
            if not page_token:
                break


# flanks/pagination.py

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class PagedResponse(Generic[T]):
    items: list[T]
    next_page_token: str | None

    def has_next(self) -> bool:
        return self.next_page_token is not None
```

## Pydantic Models

```python
# flanks/connect/models.py

from enum import Enum
from pydantic import BaseModel, ConfigDict


class FlanksModel(BaseModel):
    """Base model with lenient validation."""

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        str_strip_whitespace=True,
    )


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


class Session(FlanksModel):
    session_id: str
    status: SessionStatus
    connection_id: str | None = None
    error_code: SessionErrorCode | None = None


class SessionQuery(FlanksModel):
    model_config = ConfigDict(extra="ignore", frozen=False)

    session_id_in: list[str] | None = None
    status_in: list[SessionStatus] | None = None
    connection_id_in: list[str] | None = None
    error_code_in: list[SessionErrorCode] | None = None


class SessionConfig(FlanksModel):
    model_config = ConfigDict(extra="ignore", frozen=False)

    connector_id: str
    # ... additional config fields
```

## Usage Examples

```python
from flanks import FlanksClient

# Context manager (recommended)
async with FlanksClient() as flanks:  # Uses env vars
    # List all sessions
    async for session in flanks.connect.list_sessions():
        print(session.session_id, session.status)

    # Get entities
    entities = await flanks.entities.list()

    # Aggregation (v2 by default)
    async for product in flanks.aggregation.list_products():
        print(product)

    # Explicit v1
    portfolios = await flanks.aggregation_v1.get_portfolios(credentials_token="xxx")

# Long-lived client
flanks = FlanksClient(
    client_id="xxx",
    client_secret="yyy",
    version="2025-01-01",  # Use v1 aggregation
)
try:
    async for tx in flanks.aggregation.list_transactions():
        print(tx)
finally:
    await flanks.close()

# Raw transport access
response = await flanks.transport.api_call("/custom/endpoint", {"data": "value"})
```

## API Endpoints Coverage

### Connect API v2
- `list_connectors()` → POST /connect/v2/connectors/list-connectors
- `create_session()` → POST /connect/v2/sessions/create-session
- `list_sessions()` → POST /connect/v2/sessions/list-sessions

### Entities API
- `list()` → GET /v0/bank/available

### Credentials API
- `get_status()` → POST /v0/bank/credentials/status
- `list()` → POST /v0/bank/credentials/list
- `force_sca()` → PUT /v0/bank/credentials/status
- `force_reset()` → PUT /v0/bank/credentials/status
- `force_transaction()` → PUT /v0/bank/credentials/status
- `delete()` → DELETE /v0/bank/credentials

### Aggregation API v1
- `get_portfolios()` → POST /v0/bank/credentials/portfolio
- `get_investments()` → POST /v0/bank/credentials/investment
- `get_investment_transactions()` → POST /v0/bank/credentials/investment/transaction
- `get_accounts()` → POST /v0/bank/credentials/account
- `get_account_transactions()` → POST /v0/bank/credentials/data
- `get_liabilities()` → POST /v0/bank/credentials/liability
- `get_liability_transactions()` → POST /v0/bank/credentials/liability/transaction
- `get_cards()` → POST /v0/bank/credentials/card
- `get_card_transactions()` → POST /v0/bank/credentials/card/transaction
- `get_identity()` → POST /v0/bank/credentials/auth/
- `get_holders()` → POST /v0/bank/credentials/holder

### Aggregation API v2
- `list_products()` → POST /aggregation/v2/list-products
- `set_product_labels()` → POST /aggregation/v2/set-product-labels
- `list_transactions()` → POST /aggregation/v2/list-transactions
- `set_transaction_labels()` → POST /aggregation/v2/set-transaction-labels

### Links API (legacy)
- `list()` → GET /v0/links/list-links
- `create()` → POST /v0/links/create-link
- `edit()` → POST /v0/links/edit-link
- `delete()` → POST /v0/links/delete-link
- `pause()` → POST /v0/links/pause-link
- `resume()` → POST /v0/links/resume-link
- `get_unused_codes()` → GET /v0/platform/link
- `exchange_code()` → POST /v0/platform/link

### Report API (beta)
- `list_templates()` → GET /report/v1/list-templates
- `build_report()` → POST /report/v1/build-report
- `get_status()` → POST /report/v1/get-report-status
- `get_content_url()` → POST /report/v1/get-report-content

## Dev Dependencies

- `pytest`
- `pytest-asyncio`
- `respx` (httpx mocking)
- `ruff` (linting/formatting)
- `mypy` (type checking)
