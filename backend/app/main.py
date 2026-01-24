from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, sync, business, analytics, users, terminals, transactions, expenses, mapping
from app.api.middleware.error_handlers import register_error_handlers, BusinessLogicError

app = FastAPI(
    title="Vending Admin v2 API",
    description="Telegram Mini App для управления вендинговым бизнесом",
    version="1.0.0",
    redirect_slashes=False  # Отключаем автоматические редиректы со слешами
)

# Register error handlers
register_error_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["User Management"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Vendista Sync"])
app.include_router(business.router, prefix="/api/v1/business", tags=["Business Entities"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics & Reports"])
app.include_router(terminals.router, prefix="/api/v1/terminals", tags=["Terminals"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(mapping.router, prefix="/api/v1/mapping", tags=["Mapping"])


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Vending Admin v2 API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check для мониторинга"""
    return {"status": "healthy"}
