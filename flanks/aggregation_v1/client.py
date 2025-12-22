from typing import Any

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
from flanks.base import BaseClient


class AggregationV1Client(BaseClient):
    """Client for Aggregation API v1."""

    async def get_portfolios(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Portfolio]:
        """Get investment portfolios."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/portfolio",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Portfolio.model_validate(item) for item in response.get("portfolios", [])]

    async def get_investments(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Investment]:
        """Get investment positions."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/investment",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Investment.model_validate(item) for item in response.get("investments", [])]

    async def get_investment_transactions(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Transaction]:
        """Get investment transactions."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/investment/transaction",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Transaction.model_validate(item) for item in response.get("transactions", [])]

    async def get_accounts(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Account]:
        """Get bank accounts."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/account",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Account.model_validate(item) for item in response.get("accounts", [])]

    async def get_account_transactions(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Transaction]:
        """Get account transactions."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/data",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Transaction.model_validate(item) for item in response.get("transactions", [])]

    async def get_liabilities(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Liability]:
        """Get liabilities (loans, mortgages)."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/liability",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Liability.model_validate(item) for item in response.get("liabilities", [])]

    async def get_liability_transactions(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Transaction]:
        """Get liability transactions."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/liability/transaction",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Transaction.model_validate(item) for item in response.get("transactions", [])]

    async def get_cards(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Card]:
        """Get credit/debit cards."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/card",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Card.model_validate(item) for item in response.get("cards", [])]

    async def get_card_transactions(
        self,
        credentials_token: str,
        **query: Any,
    ) -> list[Transaction]:
        """Get card transactions."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/card/transaction",
            {"credentials_token": credentials_token, **query},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Transaction.model_validate(item) for item in response.get("transactions", [])]

    async def get_identity(self, credentials_token: str) -> Identity | None:
        """Get account holder identity."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/auth/",
            {"credentials_token": credentials_token},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        identity_data = response.get("identity")
        return Identity.model_validate(identity_data) if identity_data else None

    async def get_holders(self, credentials_token: str) -> list[Holder]:
        """Get account holders."""
        response = await self._transport.api_call(
            "/v0/bank/credentials/holder",
            {"credentials_token": credentials_token},
        )
        if not isinstance(response, dict):
            raise TypeError(f"Expected dict response, got {type(response)}")
        return [Holder.model_validate(item) for item in response.get("holders", [])]
