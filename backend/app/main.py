from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, sync, business, analytics, users

app = FastAPI(
    title="Vending Admin v2 API",
    description="Telegram Mini App для управления вендинговым бизнесом",
    version="1.0.0"
)

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
app.include_router(business.router, prefix="/api/v1", tags=["Business Entities"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics & Reports"])


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


@app.get("/status")
def connection_status():
    """Проверка статуса подключения - отвечает на 'на связи?'"""
    return {
        "status": "online",
        "message": "Да, на связи! ✅",
        "service": "Vending Admin v2 API",
        "version": "1.0.0"
    }
