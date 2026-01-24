"""
Main business API router - aggregates all business domain endpoints.
"""
from fastapi import APIRouter
from app.api.v1.locations import router as locations_router
from app.api.v1.products import router as products_router
from app.api.v1.ingredients import router as ingredients_router
from app.api.v1.drinks import router as drinks_router
from app.api.v1.inventory import router as inventory_router

router = APIRouter()

# Include all business domain routers
router.include_router(locations_router, tags=["locations"])
router.include_router(products_router, tags=["products"])
router.include_router(ingredients_router, tags=["ingredients"])
router.include_router(drinks_router, tags=["drinks"])
router.include_router(inventory_router, tags=["inventory"])


