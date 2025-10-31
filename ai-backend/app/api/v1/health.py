"""Health endpoint."""

from fastapi import APIRouter


router = APIRouter()


@router.get("/healthz")
async def health() -> dict:
    """Liveness check as per spec."""

    return {"ok": True, "version": "1.0.0"}
