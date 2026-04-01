from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.models.Map_Resources import TipoPropiedadResponse,Zona
from app.db.supabase import get_db
import requests
import time

map_resources_router = APIRouter(
    prefix="/map-resources",
    tags=["Tipo de propiedad"]
)

@map_resources_router.get("/tipos", response_model=List[TipoPropiedadResponse])
def get_type_property(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM obtener_tipos_propiedad();"))
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]

@map_resources_router.get("/zonas", response_model=List[Zona])
def get_zonas(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM obtener_zonas();"))
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]




@map_resources_router.post("/ubicacion")
def cargar_ubicaciones(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT id_zona, nombre_zona FROM zona WHERE ubicacion_geografica IS NULL"))
    zonas = result.fetchall()

    actualizadas = []

    for zona in zonas:
        nombre = zona.nombre_zona
        query = f"{nombre}, Cochabamba, Bolivia"

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }

        headers = {
            "User-Agent": "mi_app_fastapi"
        }

        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()

            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])

                db.execute(
                    text("SELECT actualizar_zona_geometria(:id, :lat, :lon)"),
                    {"id": zona.id_zona, "lat": lat, "lon": lon}
                )
                db.commit()

                actualizadas.append({
                    "zona": nombre,
                    "lat": lat,
                    "lon": lon
                })

        time.sleep(1)

    return {
        "total_actualizadas": len(actualizadas),
        "detalle": actualizadas
    }