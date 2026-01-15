"""
Vendista synchronization service.
Handles syncing transactions from Vendista API to local database.
"""
from datetime import datetime, timedelta
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
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> SyncResult:
        """
        Sync ALL transactions from Vendista DEFEN API into vendista_tx_raw table.
        Handles pagination automatically.
        IDEMPOTENT: uses ON CONFLICT DO NOTHING and client-side deduplication.

        Args:
            db: Database session
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            SyncResult with sync status and count
        """
        logger.info(f"Starting full Vendista sync (from={from_date}, to={to_date})")

        try:
            # Fetch all transactions from Vendista API
            transactions = await vendista_client.get_paginated_transactions(
                from_date=from_date,
                to_date=to_date
            )

            logger.info(f"Received {len(transactions)} transactions from Vendista API")

            if not transactions:
                logger.info("No transactions to sync")
                return SyncResult(
                    success=True,
                    transactions_synced=0,
                    fetched=0,
                    skipped_duplicates=0,
                    error_message=None
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
                    transactions_synced=0,
                    fetched=len(transactions),
                    skipped_duplicates=skipped_duplicates,
                    error_message=None
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
                transactions_synced=inserted,
                fetched=len(transactions),
                skipped_duplicates=skipped_duplicates,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            db.rollback()
            return SyncResult(
                success=False,
                transactions_synced=0,
                fetched=0,
                skipped_duplicates=0,
                error_message=str(e)
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
