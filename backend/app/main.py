from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, donors, inventory, requests, sync  # sync ကို ထည့်ပါ
from app.config import settings

app = FastAPI(
    title=f"Blood Bank Management System - {settings.SERVER_MODE.upper()} Mode",
    description="Distributed Blood Bank POC with Auto-Sync",
    version="1.0.0",
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "defaultModelsExpandDepth": -1
    }
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(donors.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(requests.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")  # ဒီ line ထည့်ပါ

@app.get("/")
def root():
    return {
        "message": f"Blood Bank System is running in {settings.SERVER_MODE} mode",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": settings.SERVER_MODE}