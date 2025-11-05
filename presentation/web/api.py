from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.web.routers.charts_router import router as charts_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="FLY API",
        version="0.1.0",
    )

    # Aqui você poderia registrar middlewares, auth, etc.

    app.include_router(charts_router)

    return app

app = create_app()
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
