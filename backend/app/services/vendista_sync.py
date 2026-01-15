"""
Vendista synchronization service.
Handles syncing transactions from Vendista API to local database.
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.vendista import VendistaTerminal, VendistaTxRaw, SyncState
from app.services.vendista_client import vendista_client
from app.schemas.vendista import SyncResult
import logging

logger = logging.getLogger(__name__)


class VendistaSyncService:
    """
    Service for synchronizing Vendista data.
    """

    async def sync_all_from_vendista(
        self,
        db: Session,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        items_per_page: int = 50,
        order_desc: bool = True,
    ) -> SyncResult:
        """
        Sync ALL transactions from Vendista DEFEN API into vendista_tx_raw table.
        Handles pagination automatically.
        IDEMPOTENT: uses ON CONFLICT DO NOTHING and client-side deduplication.

        Args:
            db: Database session
            period_start: Start date (inclusive)
            period_end: End date (inclusive)
            items_per_page: Page size for Vendista API
            order_desc: OrderDesc flag for Vendista API

        Returns:
            SyncResult with sync status and count
        """

        # Defaults: first day of current month to today (UTC)
        today = datetime.utcnow().date()
        if period_end is None:
            period_end = today
        if period_start is None:
            period_start = today.replace(day=1)

        date_from_str = f"{period_start.strftime('%Y-%m-%d')} 00:00:00"
        date_to_str = f"{period_end.strftime('%Y-%m-%d')} 23:59:59"

        logger.info(
            "Starting full Vendista sync (DateFrom=%s, DateTo=%s, ItemsPerPage=%s, OrderDesc=%s)",
            date_from_str,
            date_to_str,
            items_per_page,
            order_desc,
        )

        try:
            # Fetch all transactions from Vendista API
            paginated = await vendista_client.get_paginated_transactions(
                date_from=date_from_str,
                date_to=date_to_str,
                items_per_page=items_per_page,
                order_desc=order_desc,
            )

            transactions = paginated.get("items", [])
            expected_total = paginated.get("expected_total", 0)
            pages_fetched = paginated.get("pages_fetched", 0)
            items_per_page_resp = paginated.get("items_per_page", items_per_page)
            last_page = paginated.get("last_page", pages_fetched)

            logger.info(
                "Received %s transactions from Vendista API (expected_total=%s, pages=%s, last_page=%s)",
                len(transactions),
                expected_total,
                pages_fetched,
                last_page,
            )

            if not transactions:
                logger.info("No transactions to sync")
                return SyncResult(
                    success=True,
                    fetched=0,
                    inserted=0,
                    skipped_duplicates=0,
                    expected_total=expected_total,
                    pages_fetched=pages_fetched,
                    items_per_page=items_per_page_resp,
                    last_page=last_page,
                    transactions_synced=0,
                    error_message=None,
                )

            # Prepare rows for bulk insert
            rows = []
            for tx in transactions:
                try:
                    vendista_tx_id = tx.get("id")
                    term_id = tx.get("term_id")
                    tx_time_str = tx.get("time")
                    
                    if not vendista_tx_id or not term_id or not tx_time_str:
                        logger.warning(f"Skipping transaction with missing fields: {tx}")
                        continue

                    try:
                        tx_time = datetime.fromisoformat(tx_time_str.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        logger.warning(f"Failed to parse tx_time '{tx_time_str}' for tx {vendista_tx_id}")
                        tx_time = datetime.utcnow()

                    rows.append({
                        "term_id": term_id,
                        "vendista_tx_id": vendista_tx_id,
                        "tx_time": tx_time,
                        "payload": tx
                    })

                except Exception as e:
                    logger.error(f"Error preparing transaction: {e}")
                    continue

            # Client-side deduplication
            seen = set()
            unique_rows = []
            for r in rows:
                key = (r["term_id"], r["vendista_tx_id"])
                if key in seen:
                    continue
                seen.add(key)
                unique_rows.append(r)

            skipped_duplicates = len(rows) - len(unique_rows)
            logger.info(f"Client-side dedupe: {len(rows)} -> {len(unique_rows)} (skipped {skipped_duplicates})")

            if not unique_rows:
                logger.info("No unique rows to insert after deduplication")
                return SyncResult(
                    success=True,
                    fetched=len(transactions),
                    inserted=0,
                    skipped_duplicates=skipped_duplicates,
                    expected_total=expected_total,
                    pages_fetched=pages_fetched,
                    items_per_page=items_per_page_resp,
                    last_page=last_page,
                    transactions_synced=0,
                    error_message=None,
                )

            # Bulk insert with ON CONFLICT DO NOTHING
            stmt = pg_insert(VendistaTxRaw).values(unique_rows)
            stmt = stmt.on_conflict_do_nothing(constraint="uq_vendista_tx")
            
            result = db.execute(stmt)
            db.commit()

            inserted = result.rowcount if result.rowcount is not None else 0
            
            logger.info(
                f"Sync completed: fetched={len(transactions)}, "
                f"inserted={inserted}, skipped_duplicates={skipped_duplicates}"
            )

            return SyncResult(
                success=True,
                fetched=len(transactions),
                inserted=inserted,
                skipped_duplicates=skipped_duplicates,
                expected_total=expected_total,
                pages_fetched=pages_fetched,
                items_per_page=items_per_page_resp,
                last_page=last_page,
                transactions_synced=inserted,
                error_message=None,
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            db.rollback()
            return SyncResult(
                success=False,
                fetched=0,
                inserted=0,
                skipped_duplicates=0,
                expected_total=0,
                pages_fetched=0,
                items_per_page=items_per_page,
                last_page=0,
                transactions_synced=0,
                error_message=str(e),
            )


    def get_sync_status(self, db: Session) -> dict:
        """
        Get overall sync status.

        Args:
            db: Database session

        Returns:
            Dict with sync information
        """
        try:
            raw_count = db.query(VendistaTxRaw).count()
            return {
                "ok": True,
                "vendista_tx_raw_count": raw_count,
                "message": f"Database has {raw_count} transactions"
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {
                "ok": False,
                "vendista_tx_raw_count": 0,
                "message": f"Error: {str(e)}"
            }


# Singleton instance
sync_service = VendistaSyncService()
