from fastapi import FastAPI
from app.routers import properties_loader

app = FastAPI()
app.include_router(properties_loader.property_router)