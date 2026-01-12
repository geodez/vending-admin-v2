"""
Vendista models for storing terminal and transaction data.
"""
from sqlalchemy import Column, BigInteger, Text, Boolean, TIMESTAMP, JSON, Integer, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base


class VendistaTerminal(Base):
    """
    Vendista terminal information.
    Stores terminals that are synced from Vendista API.
    """
    __tablename__ = "vendista_terminals"

    id = Column(BigInteger, primary_key=True, index=True)  # Vendista terminal ID
    title = Column(Text, nullable=True)  # Terminal title from Vendista
    comment = Column(Text, nullable=True)  # Human-readable comment (e.g., "Островского Терм#1")
    is_active = Column(Boolean, nullable=False, default=True)  # Is terminal active
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<VendistaTerminal(id={self.id}, comment={self.comment})>"


class VendistaTxRaw(Base):
    """
    Raw transactions from Vendista API.
    Stores all transaction data in JSONB format.
    """
    __tablename__ = "vendista_tx_raw"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    term_id = Column(BigInteger, nullable=False, index=True)  # Terminal ID
    vendista_tx_id = Column(BigInteger, nullable=False, index=True)  # Transaction ID from Vendista
    tx_time = Column(TIMESTAMP(timezone=True), nullable=False, index=True)  # Transaction timestamp
    payload = Column(JSON, nullable=False)  # Full JSON payload from Vendista
    inserted_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('term_id', 'vendista_tx_id', name='uq_vendista_tx'),
    )

    def __repr__(self):
        return f"<VendistaTxRaw(id={self.id}, term_id={self.term_id}, vendista_tx_id={self.vendista_tx_id})>"


class SyncState(Base):
    """
    Synchronization state for each terminal.
    Tracks the last sync time for each terminal to enable incremental sync.
    """
    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term_id = Column(BigInteger, unique=True, nullable=False, index=True)  # Terminal ID
    last_sync_time = Column(TIMESTAMP(timezone=True), nullable=False)  # Last successful sync timestamp
    last_tx_id = Column(BigInteger, nullable=True)  # Last transaction ID synced
    sync_status = Column(Text, nullable=False, default='idle')  # Status: 'idle', 'running', 'error'
    error_message = Column(Text, nullable=True)  # Error message if sync failed
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SyncState(term_id={self.term_id}, status={self.sync_status})>"
