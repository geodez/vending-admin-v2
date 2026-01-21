"""
Vendista DEFEN API client for fetching transaction data.
Uses token as query parameter (not Bearer auth).
Docs: https://wiki.vendista.ru/en/home/defen_api
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
import math
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
        date_from: str,
        date_to: str,
        items_per_page: int = 50,
        order_desc: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch ALL transactions with pagination using DEFEN parameters.

        Args:
            date_from: "YYYY-MM-DD HH:MM:SS"
            date_to:   "YYYY-MM-DD HH:MM:SS"
            items_per_page: Page size (default 50, per API spec)
            order_desc: Whether to sort desc by time

        Returns:
            Dict with combined items and pagination metadata:
                items: List of transactions
                expected_total: items_count from API
                items_per_page: page size returned by API
                pages_fetched: how many pages were fetched
                last_page: last page number fetched
        """

        all_items: List[Dict[str, Any]] = []
        expected_total: Optional[int] = None
        pages_fetched = 0
        last_page = 0

        page_number = 1
        order_desc_str = "true" if order_desc else "false"

        logger.info(
            "Starting Vendista pagination: DateFrom=%s, DateTo=%s, ItemsPerPage=%s, OrderDesc=%s",
            date_from,
            date_to,
            items_per_page,
            order_desc,
        )

        async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(30.0, connect=15.0)) as client:
            while True:
                params = {
                    "token": self.api_token,
                    "DateFrom": date_from,
                    "DateTo": date_to,
                    "ItemsPerPage": items_per_page,
                    "PageNumber": page_number,
                    "OrderDesc": order_desc_str,
                }

                try:
                    response = await client.get(f"{self.base_url}/transactions", params=params)
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPError as e:
                    logger.error("Vendista API page %s failed: %s", page_number, e)
                    raise

                items = data.get("items", [])
                items_count = data.get("items_count", 0) or 0
                items_per_page_resp = data.get("items_per_page", items_per_page)
                page_number_resp = data.get("page_number", page_number)

                if expected_total is None:
                    expected_total = items_count

                pages_fetched += 1
                last_page = page_number_resp

                logger.info(
                    "Page %s/%s: got %s items (count=%s, per_page=%s)",
                    page_number_resp,
                    math.ceil(items_count / items_per_page_resp) if items_per_page_resp else "?",
                    len(items),
                    items_count,
                    items_per_page_resp,
                )

                if not items:
                    # If we haven't reached expected_total but items empty -> guard
                    logger.warning(
                        "Empty items on page %s before reaching expected_total=%s; stopping",
                        page_number_resp,
                        expected_total,
                    )
                    break

                all_items.extend(items)

                total_pages = math.ceil(items_count / items_per_page_resp) if items_per_page_resp else 1

                if page_number_resp >= total_pages:
                    logger.info("Pagination finished at page %s/%s", page_number_resp, total_pages)
                    break

                page_number = page_number_resp + 1
                # Guard: ensure progress
                if page_number > total_pages + 1:
                    logger.warning("Page number exceeded total_pages (%s); breaking", total_pages)
                    break

        return {
            "items": all_items,
            "expected_total": expected_total or 0,
            "items_per_page": items_per_page_resp if 'items_per_page_resp' in locals() else items_per_page,
            "pages_fetched": pages_fetched,
            "last_page": last_page,
        }

    async def get_terminals(self) -> Dict[str, Any]:
        """
        Fetch terminals list from Vendista API.
        
        Tries multiple possible endpoints:
        - /terminals
        - /devices
        - /machines
        - /partner/terminals
        
        Returns:
            Response dict with terminals list or error
        """
        possible_endpoints = [
            "/terminals",
            "/devices", 
            "/machines",
            "/partner/terminals",
            "/api/terminals"
        ]
        
        for endpoint in possible_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                params = self._get_params()
                
                logger.info(f"Trying to fetch terminals from {url}")
                
                async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Check if response looks like terminals list
                    if isinstance(data, dict):
                        # Try common response formats
                        terminals = data.get("items") or data.get("terminals") or data.get("devices") or data.get("data")
                        if terminals is not None:
                            logger.info(f"Successfully fetched terminals from {endpoint}: {len(terminals) if isinstance(terminals, list) else 'unknown'} items")
                            return {
                                "success": True,
                                "endpoint": endpoint,
                                "terminals": terminals if isinstance(terminals, list) else [terminals],
                                "raw_data": data
                            }
                    elif isinstance(data, list):
                        logger.info(f"Successfully fetched terminals from {endpoint}: {len(data)} items")
                        return {
                            "success": True,
                            "endpoint": endpoint,
                            "terminals": data,
                            "raw_data": data
                        }
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.debug(f"Endpoint {endpoint} not found (404), trying next...")
                    continue
                else:
                    logger.warning(f"Error fetching from {endpoint}: {e.response.status_code}")
                    continue
            except Exception as e:
                logger.debug(f"Error trying {endpoint}: {e}")
                continue
        
        # If all endpoints failed, return error
        logger.warning("Could not find terminals endpoint in Vendista API")
        return {
            "success": False,
            "endpoint": None,
            "terminals": [],
            "raw_data": None,
            "error": "No terminals endpoint found in Vendista API"
        }


# Singleton instance
vendista_client = VendistaAPIClient()
