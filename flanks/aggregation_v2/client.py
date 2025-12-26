from collections.abc import AsyncIterator

from flanks.aggregation_v2.models import Product, ProductQuery, Transaction, TransactionQuery
from flanks.base import BaseClient
from flanks.pagination import PagedResponse


class AggregationV2Client(BaseClient):
    """Client for Aggregation API v2.

    See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/
    """

    async def list_products(
        self,
        query: ProductQuery | None = None,
    ) -> AsyncIterator[Product]:
        """Iterate over all products matching query.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/#list-products
        """
        async for product in self._paginate(
            "/aggregation/v2/list-products",
            {"query": query.model_dump(exclude_none=True) if query else {}},
            "items",
            Product,
        ):
            yield product

    async def list_products_page(
        self,
        query: ProductQuery | None = None,
        page_token: str | None = None,
    ) -> PagedResponse[Product]:
        """Fetch a single page of products.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/#list-products
        """
        response = await self.transport.api_call(
            "/aggregation/v2/list-products",
            {
                "query": query.model_dump(exclude_none=True) if query else {},
                "page_token": page_token,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return PagedResponse(
            items=[Product.model_validate(item) for item in response["items"]],
            next_page_token=response.get("next_page_token"),
        )

    async def set_product_labels(self, product_id: str, labels: dict[str, str]) -> None:
        """Set labels on a product.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/#set-product-labels
        """
        await self.transport.api_call(
            "/aggregation/v2/set-product-labels",
            {
                "product_id": product_id,
                "labels": labels,
            },
        )

    async def list_transactions(
        self,
        query: TransactionQuery | None = None,
    ) -> AsyncIterator[Transaction]:
        """Iterate over all transactions matching query.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/#list-transactions
        """
        async for transaction in self._paginate(
            "/aggregation/v2/list-transactions",
            {"query": query.model_dump(exclude_none=True, mode="json") if query else {}},
            "items",
            Transaction,
        ):
            yield transaction

    async def list_transactions_page(
        self,
        query: TransactionQuery | None = None,
        page_token: str | None = None,
    ) -> PagedResponse[Transaction]:
        """Fetch a single page of transactions.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/#list-transactions
        """
        response = await self.transport.api_call(
            "/aggregation/v2/list-transactions",
            {
                "query": query.model_dump(exclude_none=True, mode="json") if query else {},
                "page_token": page_token,
            },
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return PagedResponse(
            items=[Transaction.model_validate(item) for item in response["items"]],
            next_page_token=response.get("next_page_token"),
        )

    async def set_transaction_labels(self, transaction_id: str, labels: dict[str, str]) -> None:
        """Set labels on a transaction.

        See: https://docs.flanks.io/pages/flanks-apis/aggregation-api/v2/#set-transaction-labels
        """
        await self.transport.api_call(
            "/aggregation/v2/set-transaction-labels",
            {
                "transaction_id": transaction_id,
                "labels": labels,
            },
        )
