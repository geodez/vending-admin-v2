"""
API endpoints for Mapping (drinks + machine_matrix).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== DRINKS SCHEMAS =====
class DrinkCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    purchase_price_rub: Optional[float] = Field(None, ge=0)
    sale_price_rub: Optional[float] = Field(None, ge=0)
    is_active: bool = True


class DrinkResponse(BaseModel):
    id: int
    name: str
    purchase_price_rub: Optional[float]
    sale_price_rub: Optional[float]
    is_active: bool


# ===== MACHINE MATRIX SCHEMAS =====
class MachineMatrixCreate(BaseModel):
    term_id: int
    machine_item_id: int
    drink_id: int
    location_id: int
    is_active: bool = True


class MachineMatrixResponse(BaseModel):
    id: int
    term_id: int
    machine_item_id: int
    drink_id: int
    location_id: int
    is_active: bool


# ===== DRINKS ENDPOINTS =====

@router.get("/drinks", response_model=List[DrinkResponse])
async def get_drinks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all drinks.
    """
    query = text("""
        SELECT id, name, purchase_price_rub, sale_price_rub, is_active
        FROM drinks
        ORDER BY name
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    drinks = []
    for row in rows:
        drinks.append({
            "id": row[0],
            "name": row[1],
            "purchase_price_rub": float(row[2]) if row[2] else None,
            "sale_price_rub": float(row[3]) if row[3] else None,
            "is_active": row[4]
        })
    
    return drinks


@router.post("/drinks", response_model=DrinkResponse, status_code=status.HTTP_201_CREATED)
async def create_drink(
    drink: DrinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new drink.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can create drinks"
        )
    
    query = text("""
        INSERT INTO drinks (name, purchase_price_rub, sale_price_rub, is_active)
        VALUES (:name, :purchase_price_rub, :sale_price_rub, :is_active)
        RETURNING id, name, purchase_price_rub, sale_price_rub, is_active
    """)
    
    result = db.execute(query, {
        "name": drink.name,
        "purchase_price_rub": drink.purchase_price_rub,
        "sale_price_rub": drink.sale_price_rub,
        "is_active": drink.is_active
    })
    db.commit()
    
    row = result.fetchone()
    
    return {
        "id": row[0],
        "name": row[1],
        "purchase_price_rub": float(row[2]) if row[2] else None,
        "sale_price_rub": float(row[3]) if row[3] else None,
        "is_active": row[4]
    }


# ===== MACHINE MATRIX ENDPOINTS =====

@router.get("/machine-matrix", response_model=List[MachineMatrixResponse])
async def get_machine_matrix(
    term_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get machine matrix (mapping of terminal buttons to drinks).
    
    Optional filter by term_id.
    """
    where_clause = "WHERE term_id = :term_id" if term_id else ""
    params = {"term_id": term_id} if term_id else {}
    
    query = text(f"""
        SELECT id, term_id, machine_item_id, drink_id, location_id, is_active
        FROM machine_matrix
        {where_clause}
        ORDER BY term_id, machine_item_id
    """)
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    matrix = []
    for row in rows:
        matrix.append({
            "id": row[0],
            "term_id": row[1],
            "machine_item_id": row[2],
            "drink_id": row[3],
            "location_id": row[4],
            "is_active": row[5]
        })
    
    return matrix


@router.post("/machine-matrix/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_machine_matrix(
    items: List[MachineMatrixCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk insert/update machine matrix records.
    
    Uses ON CONFLICT to upsert by (term_id, machine_item_id).
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can modify machine matrix"
        )
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No items provided"
        )
    
    # Prepare bulk insert
    query = text("""
        INSERT INTO machine_matrix (term_id, machine_item_id, drink_id, location_id, is_active)
        VALUES (:term_id, :machine_item_id, :drink_id, :location_id, :is_active)
        ON CONFLICT (term_id, machine_item_id)
        DO UPDATE SET
            drink_id = EXCLUDED.drink_id,
            location_id = EXCLUDED.location_id,
            is_active = EXCLUDED.is_active
    """)
    
    for item in items:
        db.execute(query, {
            "term_id": item.term_id,
            "machine_item_id": item.machine_item_id,
            "drink_id": item.drink_id,
            "location_id": item.location_id,
            "is_active": item.is_active
        })
    
    db.commit()
    
    return {"inserted": len(items), "message": "Machine matrix updated successfully"}


@router.delete("/machine-matrix/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine_matrix(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a machine matrix record.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete machine matrix records"
        )
    
    query = text("DELETE FROM machine_matrix WHERE id = :matrix_id")
    result = db.execute(query, {"matrix_id": matrix_id})
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matrix record not found"
        )
    
    return None
