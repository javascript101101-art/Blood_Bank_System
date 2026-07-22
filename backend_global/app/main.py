from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, sync_global, admin, global_requests  # ✅ အကုန်တစ်ခါတည်း
from app.config import settings

app = FastAPI(
    title=f"Blood Bank Global Server - {settings.SERVER_MODE.upper()} Mode",
    description="Central Global Server for Blood Bank System",
    version="1.0.0",
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "defaultModelsExpandDepth": -1
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(sync_global.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(global_requests.router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": f"Global Blood Bank System is running in {settings.SERVER_MODE} mode",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": settings.SERVER_MODE}