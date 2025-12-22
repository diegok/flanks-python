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
