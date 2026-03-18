import requests
from time import sleep
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.supabase import get_db
from app.models.Interest_Point import PuntoInteres,PuntoSeleccionado,PuntoEncontrado

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
        ("amenity", "school"): "colegio",
        ("amenity", "university"): "universidad",
        ("amenity", "hospital"): "hospital",
        ("amenity", "clinic"): "clinica",
        ("amenity", "healthcare"): "centro de salud",
        ("amenity", "pharmacy"): "farmacia",
        ("amenity", "marketplace"): "mercado",
        ("shop", "supermarket"): "supermercado",
        ("amenity", "bank"): "banco",
        ("amenity", "atm"): "cajero automatico",
        ("leisure", "park"): "parque",
        ("place", "square"): "plaza",
        ("shop", "mall"): "centro comercial",
        ("amenity", "restaurant"): "restaurante",
        ("highway", "bus_stop"): "transporte publico",
        ("amenity", "bus_station"): "estacion de bus",
        ("aeroway", "aerodrome"): "aeropuerto",
        ("amenity", "police"): "policia",
        ("amenity", "fire_station"): "bomberos",
        ("amenity", "place_of_worship"): "iglesia",
        ("leisure", "fitness_centre"): "gimnasio",
        ("leisure", "stadium"): "estadio",
        ("amenity", "library"): "biblioteca",
        ("tourism", "museum"): "museo",
        ("tourism", "hotel"): "hotel"
    }

    bbox = "(-17.50,-66.30,-17.30,-66.05)"
    overpass_url = "https://overpass-api.de/api/interpreter"

    filtros = []
    for (k, v) in osm_map.keys():
        filtros.append(f'node["{k}"="{v}"]{bbox};')
        filtros.append(f'way["{k}"="{v}"]{bbox};')
        filtros.append(f'relation["{k}"="{v}"]{bbox};')

    query = f"""
    [out:json][timeout:120];
    (
        {"".join(filtros)}
    );
    out center;
    """

    insertados = 0
    omitidos = 0
    vistos = set()

    try:
        response = requests.get(overpass_url, params={"data": query})

        if response.status_code != 200:
            return {"mensaje": "Error en Overpass", "insertados": 0, "omitidos": 0}

        data = response.json()

        for elemento in data.get("elements", []):

            tags = elemento.get("tags", {})
            nombre = tags.get("name")

            if not nombre:
                omitidos += 1
                continue

            lat = elemento.get("lat")
            lon = elemento.get("lon")

            if not lat or not lon:
                center = elemento.get("center")
                if center:
                    lat = center.get("lat")
                    lon = center.get("lon")

            if not lat or not lon:
                omitidos += 1
                continue

            key = None
            value = None

            for (k, v) in osm_map.keys():
                if tags.get(k) == v:
                    key = k
                    value = v
                    break

            if not key:
                omitidos += 1
                continue

            tipo_nombre = osm_map.get((key, value))
            id_tipo = tipo_map.get(tipo_nombre)

            if not id_tipo:
                omitidos += 1
                continue

            hash_unico = f"{nombre}_{round(lat,6)}_{round(lon,6)}"

            if hash_unico in vistos:
                omitidos += 1
                continue

            vistos.add(hash_unico)

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
                        "lat": lat,
                        "lon": lon,
                        "id_tipo": id_tipo
                    }
                )

                insertados += 1

            except Exception:
                omitidos += 1

    except Exception as e:
        return {"mensaje": f"Error: {str(e)}", "insertados": 0, "omitidos": 0}

    db.commit()

    return {
        "mensaje": "Carga completada",
        "insertados": insertados,
        "omitidos": omitidos
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
        LIMIT 250
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

@interest_point_router.post("/puntos-cercanos", response_model=list[PuntoEncontrado])
def encontrar_puntos_cercanos(
    punto: PuntoSeleccionado,
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT 
                pi.nombre,
                pi.latitud,
                pi.longitud,
                t.nombre_tipo,
                pi.distancia_metros
            FROM puntos_interes_cercanos(:lat, :lon, :radio) pi
            JOIN tipo_punto_interes t
                ON pi.id_tipo_punto_interes = t.id_tipo_punto_interes
            ORDER BY pi.distancia_metros ASC
            LIMIT 100
        """),
        {
            "lat": punto.latitud,
            "lon": punto.longitud,
            "radio": punto.radio
        }
    ).fetchall()

    return [
        {
            "nombre": r.nombre,
            "latitud": r.latitud,
            "longitud": r.longitud,
            "tipoPuntoInteres": r.nombre_tipo
        }
        for r in result
    ]