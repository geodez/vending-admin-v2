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

    async def sync_terminal(
        self,
        db: Session,
        term_id: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        force: bool = False
    ) -> SyncResult:
        """
        Sync transactions for a single terminal.

        Args:
            db: Database session
            term_id: Terminal ID to sync
            from_date: Start date (if None, uses last_sync_time from sync_state)
            to_date: End date (if None, uses current time)
            force: Force re-sync even if already synced

        Returns:
            SyncResult with sync status
        """
        logger.info(f"Starting sync for terminal {term_id}")

        try:
            # Get or create sync state
            sync_state = db.query(SyncState).filter(SyncState.term_id == term_id).first()

            if sync_state is None:
                # First sync - create sync state
                sync_state = SyncState(
                    term_id=term_id,
                    last_sync_time=datetime.utcnow() - timedelta(days=30),  # Default: last 30 days
                    sync_status='idle'
                )
                db.add(sync_state)
                db.commit()
                logger.info(f"Created new sync state for terminal {term_id}")

            # Determine date range
            if from_date is None:
                from_date = sync_state.last_sync_time if not force else datetime.utcnow() - timedelta(days=30)

            if to_date is None:
                to_date = datetime.utcnow()

            # Update sync state to 'running'
            sync_state.sync_status = 'running'
            sync_state.error_message = None
            db.commit()

            # Fetch transactions from Vendista API
            logger.info(f"Fetching transactions for terminal {term_id}: {from_date} to {to_date}")
            transactions = await vendista_client.get_terminal_transactions_paginated(
                term_id=term_id,
                from_date=from_date,
                to_date=to_date
            )

            logger.info(f"Received {len(transactions)} transactions for terminal {term_id}")

            # Insert transactions into database
            inserted_count = 0
            for tx in transactions:
                try:
                    # Check if transaction already exists
                    existing_tx = db.query(VendistaTxRaw).filter(
                        and_(
                            VendistaTxRaw.term_id == term_id,
                            VendistaTxRaw.vendista_tx_id == tx.id
                        )
                    ).first()

                    if existing_tx is None or force:
                        if existing_tx:
                            # Update existing transaction if force=True
                            existing_tx.tx_time = tx.timestamp
                            existing_tx.payload = tx.payload
                        else:
                            # Insert new transaction
                            new_tx = VendistaTxRaw(
                                term_id=term_id,
                                vendista_tx_id=tx.id,
                                tx_time=tx.timestamp,
                                payload=tx.payload
                            )
                            db.add(new_tx)

                        inserted_count += 1

                except Exception as e:
                    logger.error(f"Error inserting transaction {tx.id} for terminal {term_id}: {e}")
                    # Continue with next transaction

            # Commit all transactions
            db.commit()
            logger.info(f"Inserted/updated {inserted_count} transactions for terminal {term_id}")

            # Update sync state
            sync_state.last_sync_time = to_date
            sync_state.sync_status = 'idle'
            if transactions:
                sync_state.last_tx_id = max(tx.id for tx in transactions)
            db.commit()

            return SyncResult(
                term_id=term_id,
                success=True,
                transactions_synced=inserted_count,
                error_message=None
            )

        except Exception as e:
            logger.error(f"Sync failed for terminal {term_id}: {e}")

            # Update sync state to error
            if sync_state:
                sync_state.sync_status = 'error'
                sync_state.error_message = str(e)
                db.commit()

            return SyncResult(
                term_id=term_id,
                success=False,
                transactions_synced=0,
                error_message=str(e)
            )

    async def sync_all_terminals(
        self,
        db: Session,
        term_ids: Optional[List[int]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        force: bool = False
    ) -> List[SyncResult]:
        """
        Sync transactions for all terminals or a specific list.

        Args:
            db: Database session
            term_ids: List of terminal IDs (if None, syncs all active terminals)
            from_date: Start date
            to_date: End date
            force: Force re-sync

        Returns:
            List of SyncResult for each terminal
        """
        # Get terminals to sync
        if term_ids:
            terminals = db.query(VendistaTerminal).filter(
                VendistaTerminal.id.in_(term_ids)
            ).all()
        else:
            terminals = db.query(VendistaTerminal).filter(
                VendistaTerminal.is_active == True
            ).all()

        if not terminals:
            logger.warning("No terminals found to sync")
            return []

        logger.info(f"Starting sync for {len(terminals)} terminals")

        results = []
        for terminal in terminals:
            result = await self.sync_terminal(
                db=db,
                term_id=terminal.id,
                from_date=from_date,
                to_date=to_date,
                force=force
            )
            results.append(result)

        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        logger.info(f"Sync completed: {successful} successful, {failed} failed")

        return results

    def get_sync_status(self, db: Session, term_id: Optional[int] = None) -> List[SyncState]:
        """
        Get sync status for terminals.

        Args:
            db: Database session
            term_id: Terminal ID (if None, returns all)

        Returns:
            List of SyncState objects
        """
        query = db.query(SyncState)
        if term_id:
            query = query.filter(SyncState.term_id == term_id)
        return query.all()


# Singleton instance
sync_service = VendistaSyncService()
