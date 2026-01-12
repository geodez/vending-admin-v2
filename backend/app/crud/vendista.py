"""
CRUD operations for Vendista models.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.vendista import VendistaTerminal, VendistaTxRaw, SyncState
from app.schemas.vendista import (
    VendistaTerminalCreate,
    VendistaTerminalUpdate,
    VendistaTxRawCreate,
    SyncStateCreate,
    SyncStateUpdate
)


# ============================================================================
# Vendista Terminal CRUD
# ============================================================================

def get_terminal(db: Session, term_id: int) -> Optional[VendistaTerminal]:
    """Get terminal by ID."""
    return db.query(VendistaTerminal).filter(VendistaTerminal.id == term_id).first()


def get_terminals(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[VendistaTerminal]:
    """Get list of terminals."""
    query = db.query(VendistaTerminal)
    if is_active is not None:
        query = query.filter(VendistaTerminal.is_active == is_active)
    return query.offset(skip).limit(limit).all()


def create_terminal(db: Session, terminal: VendistaTerminalCreate) -> VendistaTerminal:
    """Create a new terminal."""
    db_terminal = VendistaTerminal(
        id=terminal.id,
        title=terminal.title,
        comment=terminal.comment,
        is_active=terminal.is_active
    )
    db.add(db_terminal)
    db.commit()
    db.refresh(db_terminal)
    return db_terminal


def update_terminal(
    db: Session,
    term_id: int,
    terminal_update: VendistaTerminalUpdate
) -> Optional[VendistaTerminal]:
    """Update terminal."""
    db_terminal = get_terminal(db, term_id)
    if db_terminal is None:
        return None

    update_data = terminal_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_terminal, field, value)

    db.commit()
    db.refresh(db_terminal)
    return db_terminal


def delete_terminal(db: Session, term_id: int) -> bool:
    """Delete terminal."""
    db_terminal = get_terminal(db, term_id)
    if db_terminal is None:
        return False

    db.delete(db_terminal)
    db.commit()
    return True


# ============================================================================
# Vendista Transaction CRUD
# ============================================================================

def get_transaction(db: Session, tx_id: int) -> Optional[VendistaTxRaw]:
    """Get transaction by ID."""
    return db.query(VendistaTxRaw).filter(VendistaTxRaw.id == tx_id).first()


def get_transactions(
    db: Session,
    term_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[VendistaTxRaw]:
    """Get list of transactions with filters."""
    query = db.query(VendistaTxRaw)

    if term_id is not None:
        query = query.filter(VendistaTxRaw.term_id == term_id)

    if from_date is not None:
        query = query.filter(VendistaTxRaw.tx_time >= from_date)

    if to_date is not None:
        query = query.filter(VendistaTxRaw.tx_time <= to_date)

    query = query.order_by(VendistaTxRaw.tx_time.desc())
    return query.offset(skip).limit(limit).all()


def count_transactions(
    db: Session,
    term_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
) -> int:
    """Count transactions with filters."""
    query = db.query(VendistaTxRaw)

    if term_id is not None:
        query = query.filter(VendistaTxRaw.term_id == term_id)

    if from_date is not None:
        query = query.filter(VendistaTxRaw.tx_time >= from_date)

    if to_date is not None:
        query = query.filter(VendistaTxRaw.tx_time <= to_date)

    return query.count()


# ============================================================================
# Sync State CRUD
# ============================================================================

def get_sync_state(db: Session, term_id: int) -> Optional[SyncState]:
    """Get sync state for terminal."""
    return db.query(SyncState).filter(SyncState.term_id == term_id).first()


def get_all_sync_states(db: Session) -> List[SyncState]:
    """Get all sync states."""
    return db.query(SyncState).all()


def create_sync_state(db: Session, sync_state: SyncStateCreate) -> SyncState:
    """Create sync state."""
    db_sync_state = SyncState(**sync_state.model_dump())
    db.add(db_sync_state)
    db.commit()
    db.refresh(db_sync_state)
    return db_sync_state


def update_sync_state(
    db: Session,
    term_id: int,
    sync_state_update: SyncStateUpdate
) -> Optional[SyncState]:
    """Update sync state."""
    db_sync_state = get_sync_state(db, term_id)
    if db_sync_state is None:
        return None

    update_data = sync_state_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sync_state, field, value)

    db.commit()
    db.refresh(db_sync_state)
    return db_sync_state
