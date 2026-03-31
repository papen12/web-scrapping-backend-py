from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.models.Property_Type import TipoPropiedadResponse
from app.db.supabase import get_db

type_property_router = APIRouter(
    prefix="/tipo-propiedad",
    tags=["Tipo de propiedad"]
)

@type_property_router.get("/", response_model=List[TipoPropiedadResponse])
def get_type_property(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM obtener_tipos_propiedad();"))
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]