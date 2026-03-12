from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.supabase import get_db
from app.models.propiedad import Propiedad
from app.schemas.Property import PropiedadResponse

property_router = APIRouter(prefix="/propiedades", tags=["Propiedades"])

@property_router.get("/", response_model=list[PropiedadResponse])
def getproperties(db: Session = Depends(get_db)):
    
    propiedades = db.query(Propiedad).all()

    return propiedades