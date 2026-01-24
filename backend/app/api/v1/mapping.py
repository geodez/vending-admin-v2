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
from app.schemas.business import (
    DrinkCreate, DrinkResponse, DrinkUpdate, DrinkItemResponse,
    ButtonMatrixCreate, ButtonMatrixUpdate, ButtonMatrixResponse, ButtonMatrixWithItems,
    ButtonMatrixItemCreate, ButtonMatrixItemUpdate, ButtonMatrixItemResponse,
    TerminalMatrixMapCreate, TerminalMatrixMapResponse
)
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
    term_name: Optional[str] = None  # Название терминала
    drink_name: Optional[str] = None  # Название напитка
    location_name: Optional[str] = None  # Название локации


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
        SELECT 
            mm.vendista_term_id,
            mm.machine_item_id,
            mm.drink_id,
            mm.location_id,
            mm.is_active,
            vt.comment as term_name,
            d.name as drink_name,
            l.name as location_name
        FROM machine_matrix mm
        LEFT JOIN vendista_terminals vt ON vt.id = mm.vendista_term_id
        LEFT JOIN drinks d ON d.id = mm.drink_id
        LEFT JOIN locations l ON l.id = mm.location_id
        {where_clause}
        ORDER BY mm.vendista_term_id, mm.machine_item_id
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
            "is_active": row[4],
            "term_name": row[5],
            "drink_name": row[6],
            "location_name": row[7]
        })
    
    return matrix


@router.post("/machine-matrix", response_model=MachineMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_machine_matrix(
    item: MachineMatrixCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update a single machine matrix record.
    
    Uses ON CONFLICT to upsert by (term_id, machine_item_id).
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can modify machine matrix"
        )
    
    # Validate drink_id exists
    drink_check = text("SELECT id FROM drinks WHERE id = :drink_id")
    drink_result = db.execute(drink_check, {"drink_id": item.drink_id})
    if not drink_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drink with id {item.drink_id} not found"
        )
    
    # Validate location_id exists
    location_check = text("SELECT id FROM locations WHERE id = :location_id")
    location_result = db.execute(location_check, {"location_id": item.location_id})
    if not location_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {item.location_id} not found"
        )
    
    # Insert or update
    query = text("""
        INSERT INTO machine_matrix (vendista_term_id, machine_item_id, drink_id, location_id, is_active)
        VALUES (:term_id, :machine_item_id, :drink_id, :location_id, :is_active)
        ON CONFLICT (vendista_term_id, machine_item_id)
        DO UPDATE SET
            drink_id = EXCLUDED.drink_id,
            location_id = EXCLUDED.location_id,
            is_active = EXCLUDED.is_active
        RETURNING vendista_term_id, machine_item_id, drink_id, location_id, is_active
    """)
    
    result = db.execute(query, {
        "term_id": item.term_id,
        "machine_item_id": item.machine_item_id,
        "drink_id": item.drink_id,
        "location_id": item.location_id,
        "is_active": item.is_active
    })
    
    db.commit()
    row = result.first()
    
    # Get names for response
    names_query = text("""
        SELECT 
            vt.comment as term_name,
            d.name as drink_name,
            l.name as location_name
        FROM machine_matrix mm
        LEFT JOIN vendista_terminals vt ON vt.id = mm.vendista_term_id
        LEFT JOIN drinks d ON d.id = mm.drink_id
        LEFT JOIN locations l ON l.id = mm.location_id
        WHERE mm.vendista_term_id = :term_id AND mm.machine_item_id = :machine_item_id
    """)
    names_result = db.execute(names_query, {
        "term_id": row[0],
        "machine_item_id": row[1]
    })
    names_row = names_result.first()
    
    return {
        "term_id": row[0],
        "machine_item_id": row[1],
        "drink_id": row[2],
        "location_id": row[3],
        "is_active": row[4],
        "term_name": names_row[0] if names_row else None,
        "drink_name": names_row[1] if names_row else None,
        "location_name": names_row[2] if names_row else None
    }


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


# ===== BUTTON MATRIX ENDPOINTS (New Template System) =====

@router.get("/button-matrices", response_model=List[ButtonMatrixResponse])
async def get_button_matrices(
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of button matrices (templates)."""
    matrices = crud.get_button_matrices(db, skip=skip, limit=limit, is_active=is_active)
    return matrices


@router.get("/button-matrices/{matrix_id}", response_model=ButtonMatrixWithItems)
async def get_button_matrix(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get button matrix with all items."""
    matrix = crud.get_button_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    items = crud.get_button_matrix_items(db, matrix_id)
    
    # Get names for items
    items_with_names = []
    for item in items:
        item_dict = {
            "machine_item_id": item.machine_item_id,
            "drink_id": item.drink_id,
            "is_active": item.is_active,
            "drink_name": None
        }
        
        if item.drink_id:
            drink_query = text("SELECT name FROM drinks WHERE id = :drink_id")
            drink_result = db.execute(drink_query, {"drink_id": item.drink_id})
            drink_row = drink_result.first()
            if drink_row:
                item_dict["drink_name"] = drink_row[0]
        
        items_with_names.append(ButtonMatrixItemResponse(**item_dict))        
    
    return ButtonMatrixWithItems(
        id=matrix.id,
        name=matrix.name,
        description=matrix.description,
        is_active=matrix.is_active,
        created_at=matrix.created_at,
        updated_at=matrix.updated_at,
        items=items_with_names
    )


@router.post("/button-matrices", response_model=ButtonMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_button_matrix(
    matrix: ButtonMatrixCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new button matrix template.
    
    Matrix name must be unique. Examples: "Jetinno JL24", "Jetinno JL28"
    """
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create matrices")
    
    # Check if matrix with this name already exists
    existing = db.execute(
        text("SELECT id FROM button_matrices WHERE name = :name"),
        {"name": matrix.name}
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Matrix with name '{matrix.name}' already exists"
        )
    
    return crud.create_button_matrix(db, matrix)


@router.put("/button-matrices/{matrix_id}", response_model=ButtonMatrixResponse)
async def update_button_matrix(
    matrix_id: int,
    matrix_update: ButtonMatrixUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update button matrix.
    
    Matrix name must be unique. Examples: "Jetinno JL24", "Jetinno JL28"
    """
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can update matrices")
    
    # Check if matrix exists
    matrix = crud.get_button_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    # If name is being updated, check uniqueness
    if matrix_update.name and matrix_update.name != matrix.name:
        existing = db.execute(
            text("SELECT id FROM button_matrices WHERE name = :name AND id != :matrix_id"),
            {"name": matrix_update.name, "matrix_id": matrix_id}
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Matrix with name '{matrix_update.name}' already exists"
            )
    
    updated_matrix = crud.update_button_matrix(db, matrix_id, matrix_update)
    return updated_matrix


@router.delete("/button-matrices/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_button_matrix(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete button matrix."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete matrices")
    
    if not crud.delete_button_matrix(db, matrix_id):
        raise HTTPException(status_code=404, detail="Matrix not found")


@router.post("/button-matrices/{matrix_id}/items", response_model=ButtonMatrixItemResponse, status_code=status.HTTP_201_CREATED)
async def create_button_matrix_item(
    matrix_id: int,
    item: ButtonMatrixItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add item to button matrix."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can modify matrices")
    
    # Check matrix exists
    matrix = crud.get_button_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    return crud.create_button_matrix_item(db, matrix_id, item)


@router.put("/button-matrices/{matrix_id}/items/{machine_item_id}", response_model=ButtonMatrixItemResponse)
async def update_button_matrix_item(
    matrix_id: int,
    machine_item_id: int,
    item_update: ButtonMatrixItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update button matrix item."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can modify matrices")
    
    item = crud.update_button_matrix_item(db, matrix_id, machine_item_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Matrix item not found")
    
    return item


@router.delete("/button-matrices/{matrix_id}/items/{machine_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_button_matrix_item(
    matrix_id: int,
    machine_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete button matrix item."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can modify matrices")
    
    if not crud.delete_button_matrix_item(db, matrix_id, machine_item_id):
        raise HTTPException(status_code=404, detail="Matrix item not found")


@router.post("/button-matrices/{matrix_id}/assign-terminals", response_model=List[TerminalMatrixMapResponse])
async def assign_terminals_to_matrix(
    matrix_id: int,
    request: TerminalMatrixMapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign terminals to a button matrix."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can assign terminals")
    
    # Check matrix exists
    matrix = crud.get_button_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    # Validate terminals exist
    for term_id in request.vendista_term_ids:
        term_check = text("SELECT id FROM vendista_terminals WHERE id = :term_id")
        term_result = db.execute(term_check, {"term_id": term_id})
        if not term_result.first():
            raise HTTPException(status_code=404, detail=f"Terminal {term_id} not found")
    
    # Assign terminals
    assignments = crud.assign_terminals_to_matrix(db, matrix_id, request.vendista_term_ids)
    
    # Get names for response
    result = []
    for assignment in assignments:
        term_query = text("""
            SELECT vt.comment 
            FROM vendista_terminals vt 
            WHERE vt.id = :term_id
        """)
        term_result = db.execute(term_query, {"term_id": assignment.vendista_term_id})
        term_row = term_result.first()
        
        result.append(TerminalMatrixMapResponse(
            matrix_id=assignment.matrix_id,
            matrix_name=matrix.name,
            vendista_term_id=assignment.vendista_term_id,
            term_name=term_row[0] if term_row else None,
            is_active=assignment.is_active,
            created_at=assignment.created_at
        ))
    
    return result


@router.get("/button-matrices/{matrix_id}/terminals", response_model=List[TerminalMatrixMapResponse])
async def get_matrix_terminals(
    matrix_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get terminals assigned to a matrix."""
    matrix = crud.get_button_matrix(db, matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    
    assignments = crud.get_terminal_matrix_maps(db, matrix_id=matrix_id)
    
    result = []
    for assignment in assignments:
        term_query = text("""
            SELECT vt.comment 
            FROM vendista_terminals vt 
            WHERE vt.id = :term_id
        """)
        term_result = db.execute(term_query, {"term_id": assignment.vendista_term_id})
        term_row = term_result.first()
        
        result.append(TerminalMatrixMapResponse(
            matrix_id=assignment.matrix_id,
            matrix_name=matrix.name,
            vendista_term_id=assignment.vendista_term_id,
            term_name=term_row[0] if term_row else None,
            is_active=assignment.is_active,
            created_at=assignment.created_at
        ))
    
    return result


@router.delete("/button-matrices/{matrix_id}/terminals/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_terminal_from_matrix(
    matrix_id: int,
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove terminal from matrix."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can modify matrices")
    
    if not crud.remove_terminal_from_matrix(db, matrix_id, term_id):
        raise HTTPException(status_code=404, detail="Terminal assignment not found")