from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.supabase import get_db
from app.models.propiedad import Propiedad
from app.schemas.Property import PropiedadCreate,PropiedadResponse

property_router = APIRouter(prefix="/propiedades", tags=["Propiedades"])

@property_router.get("/", response_model=list[PropiedadResponse])
def getproperties(db: Session = Depends(get_db)):
    
    propiedades = db.query(Propiedad).all()

    return propiedades
@property_router.post("/")
def crear_propiedad(propiedad: PropiedadCreate, db: Session = Depends(get_db)):

    query = text("""
        SELECT crear_propiedad(
            :nombre,
            :descripcion,
            :direccion,
            :lat,
            :lon,
            :construccion,
            :terreno,
            :precio,
            :moneda,
            :cambio,
            :zona,
            :tipo
        )
    """)
    result = db.execute(query, {
        "nombre": propiedad.nombre_propiedad,
        "descripcion": propiedad.descripcion,
        "direccion": propiedad.direccion,
        "lat": propiedad.latitud,
        "lon": propiedad.longitud,
        "construccion": propiedad.construccion_m2,
        "terreno": propiedad.terreno_m2,
        "precio": propiedad.precio_original,
        "moneda": propiedad.tipo_moneda,
        "cambio": propiedad.cambio_utilizado,
        "zona": propiedad.id_zona,
        "tipo": propiedad.id_tipo_propiedad
    })

    db.commit()

    id_propiedad = result.scalar()

    return {
        "mensaje": "Propiedad creada correctamente",
        "id_propiedad": id_propiedad
    }