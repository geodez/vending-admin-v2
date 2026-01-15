"""
Vendista DEFEN API client for fetching transaction data.
Uses token as query parameter (not Bearer auth).
Docs: https://wiki.vendista.ru/en/home/defen_api
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class VendistaAPIClient:
    """
    Asynchronous client for Vendista DEFEN API.
    Docs: https://wiki.vendista.ru/en/home/defen_api
    Endpoint: https://api.vendista.ru:99/transactions
    Auth: token as query parameter
    """

    def __init__(self):
        self.base_url = settings.vendista_api_base_url
        self.api_token = settings.vendista_api_token
        self.timeout = 30.0

    def _get_params(self, **kwargs) -> dict:
        """Get query parameters with token."""
        params = {"token": self.api_token}
        params.update(kwargs)
        return params

    async def get_transactions(
        self,
        limit: int = 1000,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fetch transactions from Vendista DEFEN API.

        Args:
            limit: Items per page (default: 1000, max: 1000)
            offset: Pagination offset (default: 0)
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            Response dict with items, page_number, items_count, items_per_page, success

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/transactions"
        params = self._get_params(
            limit=min(limit, 1000),
            offset=offset
        )
        
        # Add date filters if provided
        if from_date:
            params["period_start"] = from_date.isoformat()
        if to_date:
            params["period_end"] = to_date.isoformat()

        logger.info(
            f"Fetching transactions: limit={limit}, offset={offset}, "
            f"from={from_date}, to={to_date}"
        )

        try:
            async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                logger.info(
                    f"Received {len(data.get('items', []))} transactions, "
                    f"total_count={data.get('items_count', 0)}"
                )
                return data
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch transactions: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching transactions: {e}")
            raise

    async def test_connection(self) -> bool:
        """
        Test connection to Vendista API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/transactions"
            params = self._get_params(limit=1)
            
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                logger.info("Vendista API connection test successful")
                return True
        except Exception as e:
            logger.error(f"Vendista API connection test failed: {e}")
            return False

    async def get_paginated_transactions(
        self,
        limit: int = 1000,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch ALL transactions with pagination.
        Automatically fetches all pages and combines results.

        Args:
            limit: Items per page (default: 1000, max: 1000)
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            Combined list of all transaction items
        """
        all_items = []
        offset = 0
        page = 1

        logger.info(
            f"Starting paginated fetch: limit={limit}, "
            f"from={from_date}, to={to_date}"
        )

        while True:
            try:
                response = await self.get_transactions(
                    limit=limit,
                    offset=offset,
                    from_date=from_date,
                    to_date=to_date
                )
                
                items = response.get("items", [])
                if not items:
                    logger.info(f"Page {page}: 0 items, stopping pagination")
                    break
                
                all_items.extend(items)
                items_count = response.get("items_count", 0)
                logger.info(
                    f"Page {page}: fetched {len(items)} items, "
                    f"total so far: {len(all_items)}/{items_count}"
                )
                
                # Check if we've fetched all items
                if len(all_items) >= items_count:
                    logger.info(f"Pagination complete: {len(all_items)} total items")
                    break
                
                offset += limit
                page += 1
                
            except httpx.HTTPError as e:
                logger.error(f"Error on page {page}, offset {offset}: {e}")
                # Continue with next batch or return what we have
                if all_items:
                    logger.warning(f"Returning partial results: {len(all_items)} items")
                    break
                raise

        return all_items


# Singleton instance
vendista_client = VendistaAPIClient()
