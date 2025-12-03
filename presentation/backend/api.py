# presentation/backend/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.backend.routers.charts import router as charts_router
from presentation.backend.routers.companies import router as companies_router
from presentation.backend.routers.account_charts import (
    router as account_charts_router,
)
from presentation.backend.routers.ratios_charts import (
    router as ratios_charts_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="FLY Web API",
        version="0.1.0",
    )

    # CORS para permitir o frontend do Vite (http://localhost:5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Camada de apresentação: apenas inclui routers finos
    app.include_router(charts_router)
    app.include_router(account_charts_router)
    app.include_router(ratios_charts_router)
    app.include_router(companies_router)

    return app


app = create_app()
