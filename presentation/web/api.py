from fastapi import FastAPI
from presentation.web.routers import charts_router

app = FastAPI()
app.include_router(charts_router.router)
