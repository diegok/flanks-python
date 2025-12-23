import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.credentials.models import Credential, CredentialStatus, CredentialsListResponse


class TestCredentialModels:
    def test_parses_credential(self) -> None:
        credential = Credential.model_validate(
            {
                "credentials_token": "cred_123",
                "external_id": "ext_456",
                "bank": "bank_name",
                "status": "active",
            }
        )
        assert credential.credentials_token == "cred_123"
        assert credential.external_id == "ext_456"
        assert credential.status == "active"

    def test_parses_status_response(self) -> None:
        response = CredentialStatus.model_validate(
            {
                "pending": True,
                "blocked": False,
                "name": "Test Bank",
                "sca_token": "sca_123",
            }
        )
        assert response.pending is True
        assert response.blocked is False
        assert response.name == "Test Bank"
        assert response.sca_token == "sca_123"


class TestCredentialsClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "pending": False,
                    "blocked": False,
                    "name": "My Bank",
                    "last_update": "2024-01-15T10:00:00Z",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            status = await client.credentials.get_status("cred_123")

        assert status.pending is False
        assert status.name == "My Bank"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_credentials(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/list").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {"credentials_token": "c1", "bank": "Bank A", "status": "active"},
                        {"credentials_token": "c2", "bank": "Bank B", "status": "error"},
                    ],
                    "page": 1,
                    "pages": 2,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            response = await client.credentials.list(page=1)

        assert isinstance(response, CredentialsListResponse)
        assert len(response.items) == 2
        assert response.items[0].credentials_token == "c1"
        assert response.page == 1
        assert response.pages == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_force_sca(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.put("https://api.test.flanks.io/v0/bank/credentials/status").mock(
            return_value=httpx.Response(
                200,
                json={"sca_token": "sca_token_123"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            sca_token = await client.credentials.force_sca("cred_123")

        assert sca_token == "sca_token_123"

        # Verify request uses 'force' parameter
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["force"] == "sca"
        assert request_body["credentials_token"] == "cred_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_force_reset(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.put("https://api.test.flanks.io/v0/bank/credentials/status").mock(
            return_value=httpx.Response(
                200,
                json={"reset_token": "reset_token_123"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            reset_token = await client.credentials.force_reset("cred_123")

        assert reset_token == "reset_token_123"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["force"] == "reset"

    @respx.mock
    @pytest.mark.asyncio
    async def test_force_transaction(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.put("https://api.test.flanks.io/v0/bank/credentials/status").mock(
            return_value=httpx.Response(
                200,
                json={"transaction_token": "tx_token_123"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            tx_token = await client.credentials.force_transaction("cred_123")

        assert tx_token == "tx_token_123"

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["force"] == "transaction"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.delete("https://api.test.flanks.io/v0/bank/credentials").mock(
            return_value=httpx.Response(200, json={"message": "Successfully deleted"})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.credentials.delete("cred_123")

        # Verify DELETE was called
        assert respx.calls.last.request.method == "DELETE"
