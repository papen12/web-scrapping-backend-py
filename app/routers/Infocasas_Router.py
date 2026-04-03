from fastapi import APIRouter, Depends
import httpx
from decimal import Decimal, ROUND_HALF_UP
from app.models.Property import PropiedadBase
from app.db.supabase import *
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import math
from bs4 import BeautifulSoup


infocasas_router=APIRouter(prefix="/infocasas",tags=["Propiedades Infocasas"])

@infocasas_router.post("/contar")
async def contar_propiedades():
    url = "https://search-service.fincaraiz.com.co/api/v1/properties/search"  

    payload = {
        "variables": {
            "rows": 1,  
            "params": {
                "country_id": 5,
                "operation_type_id": 1,
                "locations": [
                    {
                        "id": "39719324-ceb1-4f46-b4f3-b4d14e3f0e4d",
                        "type": "STATE"
                    }
                ]
            },
            "page": 1,
            "source": 0
        },
        "query": ""
    }

    headers = {
        "Content-Type": "application/json",
        "x-origin": "www.infocasas.com.bo"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        data = response.json()

    total = data["hits"]["total"]["value"]

    return {"total_propiedades": total}


infocasas_router = APIRouter(
    prefix="/infocasas",
    tags=["Propiedades Infocasas"]
)

@infocasas_router.post("/post")
async def sync_propiedades_infocasas(
    db: Session = Depends(get_db)
):
    url = "https://search-service.fincaraiz.com.co/api/v1/properties/search"

    headers = {
        "Content-Type": "application/json",
        "x-origin": "www.infocasas.com.bo"
    }

    rows = 100
    page = 1
    total_insertadas = 0

    insert_query = text("""
        INSERT INTO propiedad (
            nombre_propiedad,
            descripcion,
            direccion,
            ubicacion_geografica,
            construccion_m2,
            terreno_m2,
            precio_original,
            tipo_moneda,
            cambio_utilizado,
            url_imagen,
            id_zona,
            id_tipo_propiedad
        )
        VALUES (
            :nombre_propiedad,
            :descripcion,
            :direccion,
            CASE
                WHEN :point IS NULL THEN NULL
                ELSE postgis.ST_GeomFromText(:point, 4326)
            END,
            :construccion_m2,
            :terreno_m2,
            :precio_original,
            :tipo_moneda,
            :cambio_utilizado,
            :url_imagen,
            :id_zona,
            :id_tipo_propiedad
        )
        ON CONFLICT (nombre_propiedad) DO NOTHING
    """)

    async with httpx.AsyncClient(timeout=30) as client:

        payload = {
            "variables": {
                "rows": 1,
                "params": {
                    "country_id": 5,
                    "operation_type_id": 1,
                    "locations": [
                        {
                            "id": "39719324-ceb1-4f46-b4f3-b4d14e3f0e4d",
                            "type": "STATE"
                        }
                    ]
                },
                "page": 1,
                "source": 0
            },
            "query": ""
        }

        response = await client.post(url, json=payload, headers=headers)
        data = response.json()

        total = data["hits"]["total"]["value"]
        total_pages = math.ceil(total / rows)
        max_pages = min(total_pages, 50)

        while page <= max_pages:

            payload["variables"]["rows"] = rows
            payload["variables"]["page"] = page

            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            hits = data.get("hits", {}).get("hits", [])

            if not hits:
                break

            for item in hits:

                listing = item["_source"]["listing"]

                nombre_propiedad = listing.get("title")
                direccion = listing.get("address")

                lat = listing.get("latitude")
                lon = listing.get("longitude")

                point = None
                if lat and lon:
                    point = f"POINT({float(lon)} {float(lat)})"

                construccion_m2 = Decimal(
                    listing.get("m2Built") or 0
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                terreno_m2 = Decimal(
                    listing.get("m2Terrain") or 0
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                precio = Decimal(
                    listing.get("price_amount_usd") or 0
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                if precio <= 0 or precio > Decimal("10000000"):
                    continue

                imagenes = listing.get("images", [])
                url_imagen = imagenes[0]["image"] if imagenes else None

                id_zona = None
                zona_nombre = None
                neighbourhood = listing.get("locations", {}).get("neighbourhood", [])

                if neighbourhood:
                    zona_nombre = neighbourhood[0].get("name")

                if zona_nombre:
                    zona_result = db.execute(text("""
                        SELECT id_zona FROM zona
                        WHERE LOWER(nombre_zona) = LOWER(:nombre)
                    """), {"nombre": zona_nombre}).fetchone()

                    if zona_result:
                        id_zona = zona_result[0]
                    else:
                        id_zona = db.execute(text("""
                            INSERT INTO zona (nombre_zona)
                            VALUES (:nombre)
                            RETURNING id_zona
                        """), {"nombre": zona_nombre}).fetchone()[0]
                        db.commit()

                id_tipo_propiedad = None
                tipo_nombre = listing.get("property_type", {}).get("name")

                if tipo_nombre:
                    tipo_result = db.execute(text("""
                        SELECT id_tipo_propiedad
                        FROM tipo_propiedad
                        WHERE LOWER(nombre_tipo_propiedad) = LOWER(:nombre)
                    """), {"nombre": tipo_nombre}).fetchone()

                    if tipo_result:
                        id_tipo_propiedad = tipo_result[0]
                    else:
                        id_tipo_propiedad = db.execute(text("""
                            INSERT INTO tipo_propiedad (nombre_tipo_propiedad)
                            VALUES (:nombre)
                            RETURNING id_tipo_propiedad
                        """), {"nombre": tipo_nombre}).fetchone()[0]
                        db.commit()

                if not id_tipo_propiedad:
                    id_tipo_propiedad = 30

                if not id_zona:
                    continue

                db.execute(insert_query, {
                    "nombre_propiedad": nombre_propiedad,
                    "descripcion": listing.get("description"),
                    "direccion": direccion,
                    "point": point,
                    "construccion_m2": construccion_m2,
                    "terreno_m2": terreno_m2,
                    "precio_original": precio,
                    "tipo_moneda": "USD",
                    "cambio_utilizado": Decimal("6.96"),
                    "url_imagen": url_imagen,
                    "id_zona": id_zona,
                    "id_tipo_propiedad": id_tipo_propiedad
                })

                total_insertadas += 1

            db.commit()

            page += 1
            await asyncio.sleep(0.3)

    return {
        "message": "Infocasas sincronizado correctamente",
        "total_insertadas": total_insertadas,
        "total_detectadas": total
    }
    
    
    
    


