import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.aggregation_v1.models import (
    Account,
    Card,
    Holder,
    Identity,
    Investment,
    Liability,
    Portfolio,
    Transaction,
)


class TestAggregationV1Models:
    def test_parses_portfolio(self) -> None:
        portfolio = Portfolio.model_validate(
            {"portfolio_id": "p1", "name": "My Portfolio", "total_value": "10000.50"}
        )
        assert portfolio.portfolio_id == "p1"
        assert portfolio.name == "My Portfolio"

    def test_parses_account(self) -> None:
        account = Account.model_validate(
            {"account_id": "a1", "iban": "ES1234", "balance": "5000.00"}
        )
        assert account.account_id == "a1"
        assert account.iban == "ES1234"

    def test_parses_transaction(self) -> None:
        tx = Transaction.model_validate(
            {"transaction_id": "t1", "amount": "-100.00", "description": "Payment"}
        )
        assert tx.transaction_id == "t1"
        assert tx.description == "Payment"

    def test_parses_investment(self) -> None:
        investment = Investment.model_validate(
            {
                "investment_id": "i1",
                "portfolio_id": "p1",
                "name": "Stock ABC",
                "isin": "US1234567890",
                "quantity": "100",
                "value": "5000.00",
            }
        )
        assert investment.investment_id == "i1"
        assert investment.isin == "US1234567890"

    def test_parses_liability(self) -> None:
        liability = Liability.model_validate(
            {
                "liability_id": "l1",
                "name": "Mortgage",
                "balance": "150000.00",
                "interest_rate": "2.5",
            }
        )
        assert liability.liability_id == "l1"
        assert liability.name == "Mortgage"

    def test_parses_card(self) -> None:
        card = Card.model_validate(
            {
                "card_id": "c1",
                "name": "Visa Gold",
                "masked_number": "****1234",
                "balance": "500.00",
            }
        )
        assert card.card_id == "c1"
        assert card.masked_number == "****1234"

    def test_parses_identity(self) -> None:
        identity = Identity.model_validate(
            {"name": "John Doe", "email": "john@example.com", "phone": "+34123456789"}
        )
        assert identity.name == "John Doe"
        assert identity.email == "john@example.com"

    def test_parses_holder(self) -> None:
        holder = Holder.model_validate(
            {
                "holder_id": "h1",
                "name": "Jane Doe",
                "document_type": "DNI",
                "document_number": "12345678A",
            }
        )
        assert holder.holder_id == "h1"
        assert holder.document_type == "DNI"


class TestAggregationV1Client:
    @respx.mock
    @pytest.mark.asyncio
    async def test_get_portfolios(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/portfolio").mock(
            return_value=httpx.Response(
                200,
                json=[{"portfolio_id": "p1", "name": "Portfolio 1"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            portfolios = await client.aggregation_v1.get_portfolios("cred_token")

        assert len(portfolios) == 1
        assert portfolios[0].portfolio_id == "p1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_investments(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/investment").mock(
            return_value=httpx.Response(
                200,
                json=[{"investment_id": "i1", "name": "Stock A", "isin": "US123"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            investments = await client.aggregation_v1.get_investments("cred_token")

        assert len(investments) == 1
        assert investments[0].investment_id == "i1"
        assert investments[0].isin == "US123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_investment_transactions(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/investment/transaction").mock(
            return_value=httpx.Response(
                200,
                json=[{"transaction_id": "t1", "amount": "1000.00"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            transactions = await client.aggregation_v1.get_investment_transactions("cred_token")

        assert len(transactions) == 1
        assert transactions[0].transaction_id == "t1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_accounts(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/account").mock(
            return_value=httpx.Response(
                200,
                json=[{"account_id": "a1", "iban": "ES1234"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            accounts = await client.aggregation_v1.get_accounts("cred_token")

        assert len(accounts) == 1
        assert accounts[0].account_id == "a1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_account_transactions(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/data").mock(
            return_value=httpx.Response(
                200,
                json=[{"transaction_id": "t1", "amount": "-50.00"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            transactions = await client.aggregation_v1.get_account_transactions("cred_token")

        assert len(transactions) == 1
        assert transactions[0].transaction_id == "t1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_liabilities(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/liability").mock(
            return_value=httpx.Response(
                200,
                json=[{"liability_id": "l1", "name": "Mortgage"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            liabilities = await client.aggregation_v1.get_liabilities("cred_token")

        assert len(liabilities) == 1
        assert liabilities[0].liability_id == "l1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_liability_transactions(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/liability/transaction").mock(
            return_value=httpx.Response(
                200,
                json=[{"transaction_id": "t1", "amount": "-500.00"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            transactions = await client.aggregation_v1.get_liability_transactions("cred_token")

        assert len(transactions) == 1
        assert transactions[0].transaction_id == "t1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_cards(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/card").mock(
            return_value=httpx.Response(
                200,
                json=[{"card_id": "c1", "masked_number": "****5678"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            cards = await client.aggregation_v1.get_cards("cred_token")

        assert len(cards) == 1
        assert cards[0].card_id == "c1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_card_transactions(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/card/transaction").mock(
            return_value=httpx.Response(
                200,
                json=[{"transaction_id": "t1", "amount": "-25.00"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            transactions = await client.aggregation_v1.get_card_transactions("cred_token")

        assert len(transactions) == 1
        assert transactions[0].transaction_id == "t1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_identity(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/auth/").mock(
            return_value=httpx.Response(
                200,
                json={"name": "John Doe", "email": "john@example.com"},
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            identity = await client.aggregation_v1.get_identity("cred_token")

        assert identity is not None
        assert identity.name == "John Doe"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_identity_returns_none_when_empty(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/auth/").mock(
            return_value=httpx.Response(200, json={})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            identity = await client.aggregation_v1.get_identity("cred_token")

        assert identity is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_holders(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/v0/bank/credentials/holder").mock(
            return_value=httpx.Response(
                200,
                json=[{"holder_id": "h1", "name": "Jane Doe"}],
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            holders = await client.aggregation_v1.get_holders("cred_token")

        assert len(holders) == 1
        assert holders[0].holder_id == "h1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_portfolios_with_query(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        route = respx.post("https://api.test.flanks.io/v0/bank/credentials/portfolio").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.aggregation_v1.get_portfolios(
                "cred_token",
                query={"portfolio_id": ["p1", "p2"]},
                ignore_data_error=True,
            )

        # Verify the query structure in the request body
        import json

        request_body = json.loads(route.calls.last.request.content)
        assert request_body["credentials_token"] == "cred_token"
        assert request_body["query"] == {"portfolio_id": ["p1", "p2"]}
        assert request_body["ignore_data_error"] is True
