import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.supabase import get_db
from app.models.Interest_Point import PuntoInteres

interest_point_router = APIRouter(
    prefix="/punto-interes",
    tags=["Puntos de interes para las propiedades"]
)

@interest_point_router.post("/cargar-osm")
async def cargar_puntos_interes(db: Session = Depends(get_db)):
    tipos = db.execute(text("""
        SELECT id_tipo_punto_interes, LOWER(nombre_tipo) as nombre_tipo
        FROM tipo_punto_interes
    """)).fetchall()

    tipo_map = {t.nombre_tipo: t.id_tipo_punto_interes for t in tipos}
    osm_map = {
        "colegio": ('amenity', 'school'),
        "universidad": ('amenity', 'university'),
        "hospital": ('amenity', 'hospital'),
        "clinica": ('amenity', 'clinic'),
        "centro de salud": ('amenity', 'healthcare'),
        "farmacia": ('amenity', 'pharmacy'),
        "mercado": ('amenity', 'marketplace'),
        "supermercado": ('shop', 'supermarket'),
        "banco": ('amenity', 'bank'),
        "cajero automatico": ('amenity', 'atm'),
        "parque": ('leisure', 'park'),
        "plaza": ('place', 'square'),
        "centro comercial": ('shop', 'mall'),
        "restaurante": ('amenity', 'restaurant'),
        "transporte publico": ('highway', 'bus_stop'),
        "estacion de bus": ('amenity', 'bus_station'),
        "aeropuerto": ('aeroway', 'aerodrome'),
        "policia": ('amenity', 'police'),
        "bomberos": ('amenity', 'fire_station'),
        "iglesia": ('amenity', 'place_of_worship'),
        "gimnasio": ('leisure', 'fitness_centre'),
        "estadio": ('leisure', 'stadium'),
        "biblioteca": ('amenity', 'library'),
        "museo": ('tourism', 'museum'),
        "hotel": ('tourism', 'hotel'),
    }
    bbox = "(-17.50,-66.30,-17.30,-66.05)"
    query_parts = []
    for key, value in osm_map.values():
        query_parts.append(f'node["{key}"="{value}"]{bbox};')

    query = f"""
    [out:json][timeout:25];
    (
        {"".join(query_parts)}
    );
    out body;
    """

    overpass_url = "https://overpass-api.de/api/interpreter"

    response = requests.get(overpass_url, params={"data": query})

    if response.status_code != 200:
        return {"error": "Error consultando Overpass API"}

    data = response.json()

    insertados = 0
    omitidos = 0
    for elemento in data.get("elements", []):

        lat = elemento.get("lat")
        lon = elemento.get("lon")

        if not lat or not lon:
            omitidos += 1
            continue

        tags = elemento.get("tags", {})
        nombre = tags.get("name", "Sin nombre")

        tipo_nombre = None
        for tipo_db, (k, v) in osm_map.items():
            if tags.get(k) == v:
                tipo_nombre = tipo_db
                break

        if not tipo_nombre:
            omitidos += 1
            continue

        id_tipo = tipo_map.get(tipo_nombre)

        if not id_tipo:
            omitidos += 1
            continue

        try:
            db.execute(
                text("""
                INSERT INTO punto_interes
                (nombre, ubicacion_geografica, id_tipo_punto_interes)
                VALUES (
                    :nombre,
                    postgis.ST_SetSRID(
                        postgis.ST_MakePoint(:lon, :lat),
                        4326
                    ),
                    :id_tipo
                )
                ON CONFLICT DO NOTHING
                """),
                {
                    "nombre": nombre,
                    "lat": lon,   
                    "lon": lat,
                    "id_tipo": id_tipo
                }
            )

            insertados += 1

        except Exception:
            omitidos += 1

    db.commit()

    return {
        "mensaje": "Carga completada",
        "insertados": insertados,
        "omitidos": omitidos,
        "total_procesados": len(data.get("elements", []))
    }
    
    
@interest_point_router.get("/", response_model=list[PuntoInteres])
def obtener_puntos_interes(db: Session = Depends(get_db)):
    
    result = db.execute(text("""
        SELECT 
            id_punto_interes,
            nombre,
            postgis.ST_Y(ubicacion_geografica) as latitud,
            postgis.ST_X(ubicacion_geografica) as longitud,
            id_tipo_punto_interes
        FROM punto_interes
    """)).fetchall()

    puntos = [
        {
            "id_punto_interes": r.id_punto_interes,
            "nombre": r.nombre,
            "latitud": r.latitud,
            "longitud": r.longitud,
            "id_tipo_punto_interes": r.id_tipo_punto_interes
        }
        for r in result
    ]

    return puntos