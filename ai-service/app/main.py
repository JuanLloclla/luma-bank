from fastapi import FastAPI
from app.core.config import settings
from app.routers import ocr, biometria

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
)

app.include_router(ocr.router)
app.include_router(biometria.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}