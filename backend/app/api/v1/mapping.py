"""
API endpoints for Mapping (drinks + machine_matrix).
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.business import DrinkCreate, DrinkResponse, DrinkUpdate, DrinkItemResponse
from app.crud import business as crud
import logging
import csv
import io

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== MACHINE MATRIX SCHEMAS =====
class MachineMatrixCreate(BaseModel):
    term_id: int
    machine_item_id: int
    drink_id: int
    location_id: int
    is_active: bool = True


class MachineMatrixResponse(BaseModel):
    term_id: int
    machine_item_id: int
    drink_id: Optional[int]
    location_id: Optional[int]
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
    Get list of all drinks with their recipe items (ingredients) and COGS calculation.
    """
    # Get all drinks with COGS calculation
    drinks_query = text("""
        SELECT 
            d.id,
            d.name,
            d.is_active,
            d.created_at,
            COALESCE((
                SELECT SUM(
                    CASE 
                        -- Если единицы совпадают, просто умножаем
                        WHEN di.unit = i.unit THEN di.qty_per_unit * i.cost_per_unit_rub
                        -- Конвертация: рецепт в граммах, ингредиент в килограммах
                        WHEN di.unit = 'g' AND i.unit = 'kg' THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        -- Конвертация: рецепт в миллилитрах, ингредиент в литрах
                        WHEN di.unit = 'ml' AND i.unit = 'l' THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        -- Конвертация: рецепт в граммах, ингредиент в граммах (но цена за кг)
                        WHEN di.unit = 'g' AND i.unit = 'g' AND i.cost_per_unit_rub > 100 THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        -- Остальные случаи - просто умножаем (предполагаем одинаковые единицы)
                        ELSE di.qty_per_unit * i.cost_per_unit_rub
                    END
                )
                FROM drink_items di
                JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                WHERE di.drink_id = d.id
                  AND i.expense_kind = 'stock_tracked'
                  AND i.cost_per_unit_rub IS NOT NULL
            ), 0) as cogs_rub
        FROM drinks d
        ORDER BY d.name
    """)
    
    result = db.execute(drinks_query)
    drinks_rows = result.fetchall()
    
    # Get all drink items with ingredient info
    items_query = text("""
        SELECT 
            di.drink_id,
            di.ingredient_code,
            di.qty_per_unit,
            di.unit,
            i.display_name_ru,
            i.cost_per_unit_rub,
            i.unit as ingredient_unit,
            i.expense_kind
        FROM drink_items di
        JOIN ingredients i ON i.ingredient_code = di.ingredient_code
        ORDER BY di.drink_id, di.ingredient_code
    """)
    
    items_result = db.execute(items_query)
    items_rows = items_result.fetchall()
    
    # Group items by drink_id and calculate item costs
    items_by_drink = {}
    for item_row in items_rows:
        drink_id = item_row[0]
        ingredient_code = item_row[1]
        qty_per_unit = float(item_row[2]) if item_row[2] else 0
        recipe_unit = item_row[3]
        display_name_ru = item_row[4]
        cost_per_unit_rub = float(item_row[5]) if item_row[5] else None
        ingredient_unit = item_row[6]
        expense_kind = item_row[7]
        
        # Calculate cost for this item
        item_cost = None
        if cost_per_unit_rub is not None and expense_kind == 'stock_tracked':
            if recipe_unit == ingredient_unit:
                # Same units
                item_cost = qty_per_unit * cost_per_unit_rub
            elif recipe_unit == 'g' and ingredient_unit == 'kg':
                # Recipe in grams, ingredient price per kg
                item_cost = qty_per_unit * (cost_per_unit_rub / 1000.0)
            elif recipe_unit == 'ml' and ingredient_unit == 'l':
                # Recipe in ml, ingredient price per liter
                item_cost = qty_per_unit * (cost_per_unit_rub / 1000.0)
            elif recipe_unit == 'g' and ingredient_unit == 'g' and cost_per_unit_rub > 100:
                # Likely price per kg but unit is 'g'
                item_cost = qty_per_unit * (cost_per_unit_rub / 1000.0)
            else:
                # Default: assume same units
                item_cost = qty_per_unit * cost_per_unit_rub
        
        if drink_id not in items_by_drink:
            items_by_drink[drink_id] = []
        items_by_drink[drink_id].append({
            "ingredient_code": ingredient_code,
            "qty_per_unit": qty_per_unit,
            "unit": recipe_unit,
            "display_name_ru": display_name_ru,
            "cost_per_unit_rub": cost_per_unit_rub,
            "item_cost_rub": item_cost
        })
    
    # Build response
    drinks = []
    for row in drinks_rows:
        drink_id = row[0]
        cogs_rub = float(row[4]) if row[4] else 0
        drinks.append({
            "id": drink_id,
            "name": row[1],
            "is_active": row[2],
            "created_at": row[3],
            "items": items_by_drink.get(drink_id, []),
            "cogs_rub": round(cogs_rub, 2)
        })
    
    return drinks


@router.post("/drinks", response_model=DrinkResponse, status_code=status.HTTP_201_CREATED)
async def create_drink(
    drink: DrinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new drink with recipe items.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can create drinks"
        )
    
    db_drink = crud.create_drink(db, drink)
    
    # Get drink items for response
    items_query = text("""
        SELECT ingredient_code, qty_per_unit, unit
        FROM drink_items
        WHERE drink_id = :drink_id
        ORDER BY ingredient_code
    """)
    items_result = db.execute(items_query, {"drink_id": db_drink.id})
    items_rows = items_result.fetchall()
    
    items = []
    for item_row in items_rows:
        items.append({
            "ingredient_code": item_row[0],
            "qty_per_unit": float(item_row[1]) if item_row[1] else 0,
            "unit": item_row[2]
        })
    
    return {
        "id": db_drink.id,
        "name": db_drink.name,
        "is_active": db_drink.is_active,
        "created_at": db_drink.created_at,
        "items": items
    }


@router.put("/drinks/{drink_id}", response_model=DrinkResponse)
async def update_drink(
    drink_id: int,
    drink_update: DrinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a drink and its recipe items.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can update drinks"
        )
    
    db_drink = crud.update_drink(db, drink_id, drink_update)
    if not db_drink:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drink not found"
        )
    
    # Get drink items for response
    items_query = text("""
        SELECT ingredient_code, qty_per_unit, unit
        FROM drink_items
        WHERE drink_id = :drink_id
        ORDER BY ingredient_code
    """)
    items_result = db.execute(items_query, {"drink_id": db_drink.id})
    items_rows = items_result.fetchall()
    
    items = []
    for item_row in items_rows:
        items.append({
            "ingredient_code": item_row[0],
            "qty_per_unit": float(item_row[1]) if item_row[1] else 0,
            "unit": item_row[2]
        })
    
    return {
        "id": db_drink.id,
        "name": db_drink.name,
        "is_active": db_drink.is_active,
        "created_at": db_drink.created_at,
        "items": items
    }


@router.delete("/drinks/{drink_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drink(
    drink_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a drink and its recipe items.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete drinks"
        )
    
    query = text("DELETE FROM drinks WHERE id = :drink_id")
    result = db.execute(query, {"drink_id": drink_id})
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drink not found"
        )
    
    return None


@router.put("/drinks/bulk/update", response_model=dict)
async def bulk_update_drinks(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update multiple drinks (e.g., change is_active status).
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can bulk update drinks"
        )
    
    drink_ids = request.get("drink_ids", [])
    is_active = request.get("is_active")
    
    if not drink_ids:
        raise HTTPException(status_code=400, detail="No drink IDs provided")
    
    if is_active is None:
        raise HTTPException(status_code=400, detail="No update fields provided")
    
    updated_count = 0
    for drink_id in drink_ids:
        try:
            query = text("UPDATE drinks SET is_active = :is_active WHERE id = :drink_id")
            result = db.execute(query, {"drink_id": drink_id, "is_active": is_active})
            if result.rowcount > 0:
                updated_count += 1
        except Exception as e:
            logger.error(f"Error updating drink {drink_id}: {str(e)}")
    
    db.commit()
    
    return {
        "updated": updated_count,
        "total": len(drink_ids)
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
    where_clause = "WHERE vendista_term_id = :term_id" if term_id else ""
    params = {"term_id": term_id} if term_id else {}
    
    query = text(f"""
        SELECT vendista_term_id, machine_item_id, drink_id, location_id, is_active
        FROM machine_matrix
        {where_clause}
        ORDER BY vendista_term_id, machine_item_id
    """)
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    matrix = []
    for row in rows:
        matrix.append({
            "term_id": row[0],
            "machine_item_id": row[1],
            "drink_id": row[2],
            "location_id": row[3],
            "is_active": row[4]
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
        INSERT INTO machine_matrix (vendista_term_id, machine_item_id, drink_id, location_id, is_active)
        VALUES (:term_id, :machine_item_id, :drink_id, :location_id, :is_active)
        ON CONFLICT (vendista_term_id, machine_item_id)
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


@router.delete("/machine-matrix", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine_matrix(
    term_id: int = Query(..., description="Terminal ID"),
    machine_item_id: int = Query(..., description="Machine item ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a machine matrix record by term_id and machine_item_id.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete machine matrix records"
        )
    
    query = text("DELETE FROM machine_matrix WHERE vendista_term_id = :term_id AND machine_item_id = :machine_item_id")
    result = db.execute(query, {"term_id": term_id, "machine_item_id": machine_item_id})
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
        INSERT INTO machine_matrix (vendista_term_id, machine_item_id, drink_id, location_id, is_active)
        VALUES (:term_id, :machine_item_id, :drink_id, :location_id, :is_active)
        ON CONFLICT (vendista_term_id, machine_item_id)
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


