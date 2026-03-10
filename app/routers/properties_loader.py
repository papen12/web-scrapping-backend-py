from fastapi import APIRouter
from app.db import supabase
property_router=APIRouter(prefix="/propiedades" , tags=["Propiedades Remax"])


@property_router.get("/remax")
async def crearPropiedadRemax():
    return{
        "msg":"1"
    }