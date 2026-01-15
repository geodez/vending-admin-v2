"""
Vendista synchronization service.
Handles syncing transactions from Vendista API to local database.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
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

            # Insert transactions into vendista_tx_raw table (idempotent)
            inserted_count = 0
            updated_count = 0

            for tx in transactions:
                try:
                    # Extract fields from transaction dict
                    vendista_tx_id = tx.get("id")
                    term_id = tx.get("term_id")
                    tx_time_str = tx.get("time")
                    
                    if not vendista_tx_id or not term_id or not tx_time_str:
                        logger.warning(f"Skipping transaction with missing fields: {tx}")
                        continue

                    # Parse transaction time
                    try:
                        tx_time = datetime.fromisoformat(tx_time_str.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        logger.warning(f"Failed to parse tx_time '{tx_time_str}' for tx {vendista_tx_id}")
                        tx_time = datetime.utcnow()

                    # Check if transaction already exists
                    existing_tx = db.query(VendistaTxRaw).filter(
                        and_(
                            VendistaTxRaw.term_id == term_id,
                            VendistaTxRaw.vendista_tx_id == vendista_tx_id
                        )
                    ).first()

                    if existing_tx:
                        # Update existing transaction
                        existing_tx.tx_time = tx_time
                        existing_tx.payload = tx  # Store full dict as JSON
                        updated_count += 1
                        logger.debug(f"Updated transaction {vendista_tx_id} for terminal {term_id}")
                    else:
                        # Insert new transaction
                        new_tx = VendistaTxRaw(
                            term_id=term_id,
                            vendista_tx_id=vendista_tx_id,
                            tx_time=tx_time,
                            payload=tx  # Store full dict as JSON
                        )
                        db.add(new_tx)
                        inserted_count += 1
                        logger.debug(f"Inserted new transaction {vendista_tx_id} for terminal {term_id}")

                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    continue

            # Commit all changes
            db.commit()
            logger.info(
                f"Sync completed: {inserted_count} new, {updated_count} updated, "
                f"total {len(transactions)} processed"
            )

            return SyncResult(
                success=True,
                transactions_synced=inserted_count + updated_count,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return SyncResult(
                success=False,
                transactions_synced=0,
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
