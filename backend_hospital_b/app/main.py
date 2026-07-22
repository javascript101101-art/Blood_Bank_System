from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, donors, inventory, requests, sync, global_requests

app = FastAPI(
    title=f"Blood Bank Management System - {settings.SERVER_MODE.upper()} Mode",
    description="Distributed Blood Bank POC with Auto-Sync",
    version="1.0.0",
)

# ============================================
# CORS Configuration
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",   # Hospital A Frontend
        "http://localhost:5501",   # Global Admin Frontend
        "http://localhost:5502",   # Hospital B Frontend (Local)
        "http://127.0.0.1:5502",   # Hospital B Frontend (Alternative)
        "https://blood-hospital-a-frontend.onrender.com",
        "https://blood-global-admin-frontend.onrender.com",
        "https://blood-hospital-b.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Register Routers
# ============================================
app.include_router(auth.router, prefix="/api/v1")
app.include_router(donors.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(requests.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(global_requests.router, prefix="/api/v1")

# ============================================
# Root Endpoints
# ============================================
@app.get("/")
def root():
    return {
        "message": f"Blood Bank System is running in {settings.SERVER_MODE} mode",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": settings.SERVER_MODE}