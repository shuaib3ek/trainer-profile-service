from fastapi import FastAPI
from app import api

app = FastAPI(title="Format Profiles API")
app.include_router(api.router)
