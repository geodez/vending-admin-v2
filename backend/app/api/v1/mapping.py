"""
API endpoints for Mapping (drinks + machine_matrix).
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
import logging
import csv
import io

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


# ===== IMPORT SCHEMAS =====
class ImportPreviewRow(BaseModel):
    """Row for dry-run preview (no ID, no status)"""
    term_id: int
    machine_item_id: int
    drink_id: int
    location_id: int
    is_active: bool


class ImportPreviewResponse(BaseModel):
    """Dry-run preview response"""
    total_rows: int
    valid_rows: int
    errors: List[dict]  # [{"row": 2, "error": "term_id must be integer"}]
    preview: List[ImportPreviewRow]


class ImportApplyResponse(BaseModel):
    """Apply import response"""
    inserted: int
    updated: int
    errors: List[dict]
    message: str


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


# ===== HELPER FUNCTIONS =====

def _validate_and_parse_csv(csv_content: str):
    """
    Parse and validate CSV content.
    
    Expected columns: term_id, machine_item_id, drink_id, location_id, is_active
    
    Returns: (valid_rows, errors)
    - valid_rows: List[dict] with validated data
    - errors: List[dict] with {"row": line_number, "error": message}
    """
    errors = []
    valid_rows = []
    
    try:
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        if not reader.fieldnames:
            return [], [{"row": 1, "error": "CSV is empty"}]
        
        # Check required columns
        required_cols = {"term_id", "machine_item_id", "drink_id", "location_id", "is_active"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            return [], [{"row": 1, "error": f"Missing columns: {', '.join(missing)}"}]
        
        # Parse each row
        for row_num, row in enumerate(reader, start=2):
            try:
                # Validate and convert types
                term_id = int(row["term_id"].strip())
                machine_item_id = int(row["machine_item_id"].strip())
                drink_id = int(row["drink_id"].strip())
                location_id = int(row["location_id"].strip())
                is_active_str = row["is_active"].strip().lower()
                
                if is_active_str not in ("true", "false", "1", "0"):
                    raise ValueError(f"is_active must be 'true' or 'false', got '{is_active_str}'")
                
                is_active = is_active_str in ("true", "1")
                
                # Validate ranges
                if term_id <= 0:
                    raise ValueError("term_id must be positive")
                if machine_item_id <= 0:
                    raise ValueError("machine_item_id must be positive")
                if drink_id <= 0:
                    raise ValueError("drink_id must be positive")
                if location_id < 0:
                    raise ValueError("location_id must be non-negative")
                
                valid_rows.append({
                    "term_id": term_id,
                    "machine_item_id": machine_item_id,
                    "drink_id": drink_id,
                    "location_id": location_id,
                    "is_active": is_active
                })
            
            except ValueError as e:
                errors.append({"row": row_num, "error": str(e)})
            except KeyError as e:
                errors.append({"row": row_num, "error": f"Missing column: {e}"})
    
    except Exception as e:
        logger.error(f"CSV parsing error: {e}")
        return [], [{"row": 0, "error": f"CSV parsing failed: {str(e)}"}]
    
    return valid_rows, errors


# ===== IMPORT ENDPOINTS =====

# ===== IMPORT ENDPOINTS =====

@router.post("/matrix/import")
async def import_matrix(
    file: UploadFile = File(...),
    dry_run: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import machine matrix from CSV file with optional dry-run mode.
    
    CSV format:
        term_id,machine_item_id,drink_id,location_id,is_active
        178428,1,101,10,true
        178428,2,102,11,true
    
    Parameters:
    - file: CSV file upload
    - dry_run: if true (default), validate and preview only; if false, apply changes
    
    Returns:
    - dry_run=true: ImportPreviewResponse (validation errors + preview)
    - dry_run=false: ImportApplyResponse (insert/update summary)
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can import machine matrix"
        )
    
    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
    except Exception as e:
        logger.error(f"File read error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Parse and validate CSV
    valid_rows, errors = _validate_and_parse_csv(csv_content)
    
    logger.info(f"CSV import: dry_run={dry_run}, valid_rows={len(valid_rows)}, errors={len(errors)}")
    
    # DRY-RUN MODE: return preview
    if dry_run:
        preview = valid_rows[:100]  # Limit preview to 100 rows
        return ImportPreviewResponse(
            total_rows=len(valid_rows) + len(errors),
            valid_rows=len(valid_rows),
            errors=errors,
            preview=preview
        )
    
    # APPLY MODE: check for errors first
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV validation failed with {len(errors)} error(s). Fix errors and retry."
        )
    
    # Apply bulk upsert
    inserted = 0
    apply_errors = []
    
    query = text("""
        INSERT INTO machine_matrix (term_id, machine_item_id, drink_id, location_id, is_active)
        VALUES (:term_id, :machine_item_id, :drink_id, :location_id, :is_active)
        ON CONFLICT (term_id, machine_item_id)
        DO UPDATE SET
            drink_id = EXCLUDED.drink_id,
            location_id = EXCLUDED.location_id,
            is_active = EXCLUDED.is_active
    """)
    
    for row in valid_rows:
        try:
            db.execute(query, row)
        except Exception as e:
            logger.error(f"Upsert error for {row}: {e}")
            apply_errors.append({
                "term_id": row["term_id"],
                "machine_item_id": row["machine_item_id"],
                "error": str(e)
            })
    
    db.commit()
    inserted = len(valid_rows) - len(apply_errors)
    
    logger.info(f"CSV import applied: inserted={inserted}, errors={len(apply_errors)}")
    
    return ImportApplyResponse(
        inserted=inserted,
        updated=0,
        errors=apply_errors,
        message=f"Successfully imported {inserted} rows"
    )


