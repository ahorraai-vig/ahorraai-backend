from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ahorraai_vigo import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    engine = request.app.state.engine
    payload = {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": __version__,
        "database": "ok",
    }

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        payload["status"] = "degraded"
        payload["database"] = "error"
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)

    return JSONResponse(content=payload)
