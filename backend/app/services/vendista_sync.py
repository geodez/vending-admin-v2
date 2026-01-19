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

    async def sync_terminals_from_api(self, db: Session) -> dict:
        """
        Sync terminals directly from Vendista API.
        
        Tries to fetch terminals list from API endpoints.
        If API endpoint is not available, falls back to transactions method.
        
        Args:
            db: Database session
            
        Returns:
            Dict with sync result
        """
        from app.crud import vendista as crud_vendista
        from app.schemas.vendista import VendistaTerminalCreate, VendistaTerminalUpdate
        
        try:
            logger.info("Starting terminal sync from Vendista API")
            
            # Try to fetch terminals from API
            api_result = await vendista_client.get_terminals()
            
            if not api_result.get("success") or not api_result.get("terminals"):
                logger.warning("Could not fetch terminals from API, falling back to transactions method")
                return self.sync_terminals_from_transactions(db)
            
            terminals_data = api_result["terminals"]
            logger.info(f"Received {len(terminals_data)} terminals from API")
            
            synced_count = 0
            created_count = 0
            updated_count = 0
            terminals = []
            
            for term_data in terminals_data:
                try:
                    # Try to extract terminal info from different possible formats
                    term_id = term_data.get("id") or term_data.get("term_id") or term_data.get("terminal_id")
                    if not term_id:
                        logger.warning(f"Skipping terminal with missing ID: {term_data}")
                        continue
                    
                    # Try different field names for comment/title
                    comment = (
                        term_data.get("comment") or 
                        term_data.get("terminal_comment") or 
                        term_data.get("name") or 
                        term_data.get("title") or
                        term_data.get("description") or
                        None
                    )
                    
                    title = (
                        term_data.get("title") or 
                        term_data.get("terminal_id") or
                        term_data.get("device_id") or
                        None
                    )
                    
                    is_active = term_data.get("is_active", True)
                    if isinstance(is_active, str):
                        is_active = is_active.lower() in ("true", "1", "yes", "active")
                    
                    # Check if terminal already exists
                    existing_terminal = crud_vendista.get_terminal(db, term_id)
                    
                    if existing_terminal:
                        # Update existing terminal
                        needs_update = False
                        update_data_dict = {}
                        
                        if comment and existing_terminal.comment != comment:
                            update_data_dict["comment"] = comment
                            needs_update = True
                        if title and existing_terminal.title != title:
                            update_data_dict["title"] = title
                            needs_update = True
                        if existing_terminal.is_active != is_active:
                            update_data_dict["is_active"] = is_active
                            needs_update = True
                        
                        if needs_update:
                            update_data = VendistaTerminalUpdate(**update_data_dict)
                            crud_vendista.update_terminal(db, term_id, update_data)
                            updated_count += 1
                            logger.info(f"Updated terminal {term_id}: {comment or title}")
                        else:
                            logger.debug(f"Terminal {term_id} already up to date")
                    else:
                        # Create new terminal
                        terminal_data = VendistaTerminalCreate(
                            id=term_id,
                            title=title,
                            comment=comment,
                            is_active=is_active
                        )
                        crud_vendista.create_terminal(db, terminal_data)
                        created_count += 1
                        logger.info(f"Created terminal {term_id}: {comment or title}")
                    
                    synced_count += 1
                    terminals.append({
                        "id": term_id,
                        "comment": comment,
                        "title": title
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing terminal: {e}", exc_info=True)
                    continue
            
            db.commit()
            
            logger.info(
                f"Terminal sync from API completed: {synced_count} total, "
                f"{created_count} created, {updated_count} updated"
            )
            
            return {
                "success": True,
                "source": "api",
                "synced_count": synced_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "terminals": terminals,
                "message": f"Синхронизировано терминалов из API: {synced_count} (создано: {created_count}, обновлено: {updated_count})"
            }
            
        except Exception as e:
            logger.error(f"Terminal sync from API failed: {e}", exc_info=True)
            db.rollback()
            # Fallback to transactions method
            logger.info("Falling back to transactions sync method")
            return self.sync_terminals_from_transactions(db)

    def sync_terminals_from_transactions(self, db: Session) -> dict:
        """
        Sync terminals from vendista_tx_raw transactions into vendista_terminals table.
        
        Extracts unique terminals from transaction payloads and creates/updates
        terminal records with title (from terminal_comment) and comment.
        
        Args:
            db: Database session
            
        Returns:
            Dict with sync result: {success, synced_count, updated_count, created_count, terminals}
        """
        from sqlalchemy import text
        from app.crud import vendista as crud_vendista
        from app.schemas.vendista import VendistaTerminalCreate
        
        try:
            logger.info("Starting terminal sync from transactions")
            
            # Extract unique terminals from transactions
            query = text("""
                SELECT DISTINCT ON (term_id)
                    term_id,
                    MAX(payload->>'terminal_comment') as terminal_comment,
                    MAX(payload->>'terminal_id') as terminal_id
                FROM vendista_tx_raw
                WHERE term_id IS NOT NULL
                GROUP BY term_id
                ORDER BY term_id
            """)
            
            result = db.execute(query)
            terminal_rows = result.fetchall()
            
            logger.info(f"Found {len(terminal_rows)} unique terminals in transactions")
            
            synced_count = 0
            created_count = 0
            updated_count = 0
            terminals = []
            
            for row in terminal_rows:
                term_id = row.term_id
                terminal_comment = row.terminal_comment or ""
                terminal_id = row.terminal_id or ""
                
                # Check if terminal already exists
                existing_terminal = crud_vendista.get_terminal(db, term_id)
                
                if existing_terminal:
                    # Update existing terminal if comment changed
                    if existing_terminal.comment != terminal_comment:
                        from app.schemas.vendista import VendistaTerminalUpdate
                        update_data = VendistaTerminalUpdate(
                            comment=terminal_comment if terminal_comment else None
                        )
                        crud_vendista.update_terminal(db, term_id, update_data)
                        updated_count += 1
                        logger.info(f"Updated terminal {term_id}: {terminal_comment}")
                    else:
                        logger.debug(f"Terminal {term_id} already exists, skipping")
                else:
                    # Create new terminal
                    terminal_data = VendistaTerminalCreate(
                        id=term_id,
                        title=terminal_id if terminal_id else None,  # Use terminal_id as title
                        comment=terminal_comment if terminal_comment else None,
                        is_active=True
                    )
                    crud_vendista.create_terminal(db, terminal_data)
                    created_count += 1
                    logger.info(f"Created terminal {term_id}: {terminal_comment}")
                
                synced_count += 1
                terminals.append({
                    "id": term_id,
                    "comment": terminal_comment,
                    "terminal_id": terminal_id
                })
            
            db.commit()
            
            logger.info(
                f"Terminal sync completed: {synced_count} total, "
                f"{created_count} created, {updated_count} updated"
            )
            
            return {
                "success": True,
                "source": "transactions",
                "synced_count": synced_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "terminals": terminals,
                "message": f"Синхронизировано терминалов из транзакций: {synced_count} (создано: {created_count}, обновлено: {updated_count})"
            }
            
        except Exception as e:
            logger.error(f"Terminal sync failed: {e}", exc_info=True)
            db.rollback()
            return {
                "success": False,
                "source": "transactions",
                "synced_count": 0,
                "created_count": 0,
                "updated_count": 0,
                "terminals": [],
                "message": f"Ошибка синхронизации: {str(e)}"
            }


# Singleton instance
sync_service = VendistaSyncService()
