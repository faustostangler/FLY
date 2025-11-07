# presentation/backend/api.py
from __future__ import annotations

from fastapi import FastAPI

from presentation.backend.routers.charts import router as charts_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="FLY Web API",
        version="0.1.0",
    )

    # Camada de apresentação: apenas inclui routers finos
    app.include_router(charts_router)

    return app


app = create_app()
