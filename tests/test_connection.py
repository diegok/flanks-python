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
