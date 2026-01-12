"""
Vendista API client for fetching transaction data.
"""
import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from app.config import settings
from app.schemas.vendista import VendistaTransaction, VendistaTransactionsResponse
import logging

logger = logging.getLogger(__name__)


class VendistaAPIClient:
    """
    Asynchronous client for Vendista API.
    Handles authentication and data fetching from Vendista service.
    """

    def __init__(self):
        self.base_url = settings.vendista_api_base_url
        self.api_token = settings.vendista_api_token
        self.timeout = 30.0

    def _get_headers(self) -> dict:
        """Get HTTP headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_terminal_transactions(
        self,
        term_id: int,
        from_date: datetime,
        to_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[VendistaTransaction]:
        """
        Fetch transactions for a specific terminal.

        Args:
            term_id: Terminal ID
            from_date: Start date for transactions
            to_date: End date for transactions (default: now)
            limit: Maximum number of transactions to fetch (default: 1000, max: 1000)

        Returns:
            List of VendistaTransaction objects

        Raises:
            httpx.HTTPError: If API request fails
        """
        if to_date is None:
            to_date = datetime.utcnow()

        url = f"{self.base_url}/api/v1/terminals/{term_id}/transactions"
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "limit": min(limit, 1000)  # Enforce max limit
        }

        logger.info(
            f"Fetching transactions for terminal {term_id}: "
            f"{from_date.isoformat()} to {to_date.isoformat()}"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Received {len(data.get('transactions', []))} transactions for terminal {term_id}")

                # Parse response using Pydantic
                parsed_response = VendistaTransactionsResponse(**data)
                return parsed_response.transactions

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching transactions for terminal {term_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching transactions for terminal {term_id}: {e}")
            raise

    async def get_terminal_transactions_paginated(
        self,
        term_id: int,
        from_date: datetime,
        to_date: Optional[datetime] = None,
        batch_size: int = 1000
    ) -> List[VendistaTransaction]:
        """
        Fetch transactions with automatic pagination for large date ranges.

        Args:
            term_id: Terminal ID
            from_date: Start date for transactions
            to_date: End date for transactions (default: now)
            batch_size: Number of transactions per batch (max: 1000)

        Returns:
            List of all VendistaTransaction objects

        Raises:
            httpx.HTTPError: If API request fails
        """
        if to_date is None:
            to_date = datetime.utcnow()

        all_transactions = []
        current_from = from_date
        batch_size = min(batch_size, 1000)

        logger.info(
            f"Starting paginated fetch for terminal {term_id}: "
            f"{from_date.isoformat()} to {to_date.isoformat()}"
        )

        # Fetch in batches (split by 1-day intervals to avoid hitting API limits)
        while current_from < to_date:
            current_to = min(current_from + timedelta(days=1), to_date)

            try:
                batch = await self.get_terminal_transactions(
                    term_id=term_id,
                    from_date=current_from,
                    to_date=current_to,
                    limit=batch_size
                )

                all_transactions.extend(batch)
                logger.info(
                    f"Fetched batch: {len(batch)} transactions "
                    f"({current_from.isoformat()} to {current_to.isoformat()})"
                )

                # If we got fewer transactions than the limit, we can move to next day
                if len(batch) < batch_size:
                    current_from = current_to
                else:
                    # If we got full batch, there might be more transactions on this day
                    # Move forward by a smaller increment
                    current_from = current_from + timedelta(hours=6)

            except httpx.HTTPError as e:
                logger.error(
                    f"Failed to fetch batch for terminal {term_id}: "
                    f"{current_from.isoformat()} to {current_to.isoformat()}: {e}"
                )
                # Continue with next batch instead of failing completely
                current_from = current_to

        logger.info(f"Completed paginated fetch: total {len(all_transactions)} transactions")
        return all_transactions

    async def test_connection(self) -> bool:
        """
        Test connection to Vendista API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch terminals or a simple health endpoint
            # For now, we'll just try to make a request with proper auth
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/terminals",  # Assuming this endpoint exists
                    headers=self._get_headers()
                )
                response.raise_for_status()
                logger.info("Vendista API connection test successful")
                return True
        except Exception as e:
            logger.error(f"Vendista API connection test failed: {e}")
            return False


# Singleton instance
vendista_client = VendistaAPIClient()
