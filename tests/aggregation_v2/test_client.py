import datetime
from decimal import Decimal

import httpx
import pytest
import respx

from flanks import FlanksClient
from flanks.aggregation_v2.models import (
    Product,
    ProductQuery,
    ProductType,
    Transaction,
    TransactionQuery,
)
from flanks.pagination import PagedResponse


class TestAggregationV2Models:
    def test_parses_product(self) -> None:
        product = Product.model_validate(
            {
                "product_id": "prod_123",
                "product_type": "Account",
                "connection_id": "conn_456",
                "name": "Checking Account",
                "balance": "1500.50",
                "currency": "EUR",
                "iban": "ES1234567890",
                "labels": {"category": "personal"},
            }
        )
        assert product.product_id == "prod_123"
        assert product.product_type == ProductType.ACCOUNT
        assert product.connection_id == "conn_456"
        assert product.balance == Decimal("1500.50")
        assert product.labels == {"category": "personal"}

    def test_parses_transaction(self) -> None:
        transaction = Transaction.model_validate(
            {
                "transaction_id": "tx_123",
                "product_id": "prod_456",
                "amount": "-50.00",
                "currency": "EUR",
                "description": "Coffee shop",
                "date": "2024-01-15",
                "category": "Food",
                "labels": {"reviewed": "true"},
            }
        )
        assert transaction.transaction_id == "tx_123"
        assert transaction.amount == Decimal("-50.00")
        assert transaction.date == datetime.date(2024, 1, 15)
        assert transaction.labels == {"reviewed": "true"}


class TestAggregationV2Client:
    @respx.mock
    @pytest.mark.asyncio
    async def test_list_products_iterator(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        route = respx.post("https://api.test.flanks.io/aggregation/v2/list-products")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "items": [{"product_id": "p1", "product_type": "Account"}],
                    "next_page_token": "page2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"product_id": "p2", "product_type": "Card"}],
                    "next_page_token": None,
                },
            ),
        ]

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            products = [p async for p in client.aggregation_v2.list_products()]

        assert len(products) == 2
        assert products[0].product_id == "p1"
        assert products[1].product_type == ProductType.CARD

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_products_with_query(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/aggregation/v2/list-products").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"product_id": "p1", "product_type": "Account"}],
                    "next_page_token": None,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            query = ProductQuery(product_type_in=[ProductType.ACCOUNT])
            products = [p async for p in client.aggregation_v2.list_products(query)]

        assert len(products) == 1
        # Verify query was sent
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["query"]["product_type_in"] == ["Account"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_products_page(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/aggregation/v2/list-products").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"product_id": "p1", "product_type": "Account"}],
                    "next_page_token": "next_token",
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            page = await client.aggregation_v2.list_products_page()

        assert isinstance(page, PagedResponse)
        assert len(page.items) == 1
        assert page.next_page_token == "next_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_set_product_labels(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/aggregation/v2/set-product-labels").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.aggregation_v2.set_product_labels("prod_123", {"category": "savings"})

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["product_id"] == "prod_123"
        assert request_body["labels"] == {"category": "savings"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_transactions_iterator(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/aggregation/v2/list-transactions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"transaction_id": "tx1", "amount": "100.00"}],
                    "next_page_token": None,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            transactions = [t async for t in client.aggregation_v2.list_transactions()]

        assert len(transactions) == 1
        assert transactions[0].transaction_id == "tx1"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_transactions_with_query(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/aggregation/v2/list-transactions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [{"transaction_id": "tx1", "amount": "100.00"}],
                    "next_page_token": None,
                },
            )
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            query = TransactionQuery(
                product_id_in=["prod1"],
                date_from=datetime.date(2024, 1, 1),
                date_to=datetime.date(2024, 12, 31),
            )
            transactions = [t async for t in client.aggregation_v2.list_transactions(query)]

        assert len(transactions) == 1
        # Verify query
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["query"]["product_id_in"] == ["prod1"]
        assert request_body["query"]["date_from"] == "2024-01-01"
        assert request_body["query"]["date_to"] == "2024-12-31"

    @respx.mock
    @pytest.mark.asyncio
    async def test_set_transaction_labels(self) -> None:
        respx.post("https://api.test.flanks.io/v0/token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 3600, "token_type": "Bearer"},
            )
        )

        respx.post("https://api.test.flanks.io/aggregation/v2/set-transaction-labels").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        async with FlanksClient(
            client_id="id",
            client_secret="secret",
            base_url="https://api.test.flanks.io",
        ) as client:
            await client.aggregation_v2.set_transaction_labels("tx_123", {"reviewed": "true"})

        # Verify request
        import json

        request_body = json.loads(respx.calls.last.request.content)
        assert request_body["transaction_id"] == "tx_123"
        assert request_body["labels"] == {"reviewed": "true"}
