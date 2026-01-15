"""
Pydantic schemas for Vendista API and models.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, Dict, List


# ============================================================================
# Vendista API Schemas
# ============================================================================

class VendistaTransactionPayload(BaseModel):
    """Payload structure from Vendista API transaction."""
    MachineItemId: int
    Terminal_Comment: Optional[str] = Field(None, alias="Terminal Comment")
    fact_sum: float
    price: float
    product_name: Optional[str] = None

    class Config:
        populate_by_name = True


class VendistaTransaction(BaseModel):
    """Transaction structure from Vendista API."""
    id: int  # Transaction ID from Vendista
    terminal_id: int
    timestamp: datetime
    machine_item_id: int
    product_name: Optional[str] = None
    price: float
    status: str
    payload: Dict[str, Any]


class VendistaTransactionsResponse(BaseModel):
    """Response from Vendista API for transactions endpoint."""
    transactions: List[VendistaTransaction]


class VendistaTerminalInfo(BaseModel):
    """Terminal information from Vendista API."""
    id: int
    title: Optional[str] = None
    comment: Optional[str] = None
    is_active: bool = True


# ============================================================================
# Database Model Schemas
# ============================================================================

class VendistaTerminalBase(BaseModel):
    """Base schema for Vendista Terminal."""
    title: Optional[str] = None
    comment: Optional[str] = None
    is_active: bool = True


class VendistaTerminalCreate(VendistaTerminalBase):
    """Schema for creating a Vendista Terminal."""
    id: int  # Vendista terminal ID


class VendistaTerminalUpdate(BaseModel):
    """Schema for updating a Vendista Terminal."""
    title: Optional[str] = None
    comment: Optional[str] = None
    is_active: Optional[bool] = None


class VendistaTerminalResponse(VendistaTerminalBase):
    """Schema for Vendista Terminal response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Transaction Schemas
# ============================================================================

class VendistaTxRawBase(BaseModel):
    """Base schema for raw Vendista transaction."""
    term_id: int
    vendista_tx_id: int
    tx_time: datetime
    payload: Dict[str, Any]


class VendistaTxRawCreate(VendistaTxRawBase):
    """Schema for creating a raw Vendista transaction."""
    pass


class VendistaTxRawResponse(VendistaTxRawBase):
    """Schema for raw Vendista transaction response."""
    id: int
    inserted_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Sync State Schemas
# ============================================================================

class SyncStateBase(BaseModel):
    """Base schema for sync state."""
    term_id: int
    last_sync_time: datetime
    last_tx_id: Optional[int] = None
    sync_status: str = 'idle'  # 'idle', 'running', 'error'
    error_message: Optional[str] = None


class SyncStateCreate(SyncStateBase):
    """Schema for creating sync state."""
    pass


class SyncStateUpdate(BaseModel):
    """Schema for updating sync state."""
    last_sync_time: Optional[datetime] = None
    last_tx_id: Optional[int] = None
    sync_status: Optional[str] = None
    error_message: Optional[str] = None


class SyncStateResponse(SyncStateBase):
    """Schema for sync state response."""
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Sync Operation Schemas
# ============================================================================

class SyncRequest(BaseModel):
    """Request schema for manual sync."""
    term_ids: Optional[List[int]] = None  # List of terminal IDs to sync (None = all terminals)
    from_date: Optional[datetime] = None  # Start date for sync
    to_date: Optional[datetime] = None  # End date for sync (None = now)
    force: bool = False  # Force re-sync even if already synced


class SyncResult(BaseModel):
    """Result of sync operation with detailed metrics."""
    success: bool
    fetched: int = 0  # Total transactions fetched from API
    inserted: int = 0  # Transactions inserted into DB
    skipped_duplicates: int = 0  # Duplicates skipped (ON CONFLICT)
    expected_total: int = 0  # items_count reported by Vendista API
    pages_fetched: int = 0  # How many pages were requested
    items_per_page: int = 0  # Page size used when fetching
    last_page: int = 0  # Last page number fetched
    transactions_synced: int  # Total synced (inserted + updated)
    error_message: Optional[str] = None


class SyncResponse(BaseModel):
    """Response schema for sync operation."""
    started_at: datetime
    completed_at: datetime
    total_terminals: int
    successful: int
    failed: int
    results: List[SyncResult]
