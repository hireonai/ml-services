# In app/__init__.py
from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(
    title="ML Services API",
    description="API for machine learning services"
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
