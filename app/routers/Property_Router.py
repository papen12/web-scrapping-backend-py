from fastapi import APIRouter

from app.models.Property import PropiedadBase

property_router=APIRouter(prefix="/propiedades",tags=["Propiedades"])

@property_router.get("/")
async def getproperties():
    return{}