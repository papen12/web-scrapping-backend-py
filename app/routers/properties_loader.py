from fastapi import APIRouter, Depends
import httpx
from decimal import Decimal, ROUND_HALF_UP
from app.models.Property import PropiedadBase
from app.db.supabase import *
from sqlalchemy.orm import Session
from sqlalchemy import text


property_router = APIRouter(prefix="/propiedades", tags=["Propiedades Remax"])

@property_router.get("/remax")
async def GetPropiedadesRemax():
    url = "https://remax.bo/api/search/terreno/cochabamba"
    params = {
        "order[]": [1, 3],
        "page": 1,
        "swLat": -17.49804427435114,
        "swLng": -66.37390136718751,
        "neLat": -17.31393222192294,
        "neLng": -65.96809387207033
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        result = response.json()

    propiedades_list = []

    for item in result.get("data", []):
        if item.get("transaction_type", {}).get("name") != "Venta":
            continue

        slug = item.get("slug")
        descripcion = item.get("listing_information", {}).get("subtype_property", {}).get("name")
        direccion = item.get("location", {}).get("first_address")
        url=item.get("default_imagen",{}).get("url")
        latitud = item.get("location", {}).get("latitude")
        longitud = item.get("location", {}).get("longitude")
        terreno_m2 = Decimal(item.get("listing_information", {}).get("land_m2", 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        precio_original = Decimal(item.get("price", {}).get("amount", 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        propiedad = PropiedadBase(
            nombre_propiedad=slug,
            descripcion=descripcion,
            direccion=direccion,
            ubicacion_geografica=f"{latitud},{longitud}" if latitud and longitud else None,
            construccion_m2=Decimal(0),
            terreno_m2=terreno_m2,
            precio_original=precio_original,
            tipo_moneda="BOB",
            url_imagen=url,
            precio_bob=precio_original,
            precio_usd=None,
            cambio_utilizado=Decimal("6.86"),
            precio_m2_bob=None,
            precio_m2_usd=None,
            id_zona=1,
            id_tipo_propiedad=1
        )

        propiedades_list.append(propiedad)

    return propiedades_list






@property_router.post("/remax-post")
async def guardar_propiedad(
    propiedad: PropiedadBase,
    db: Session = Depends(get_db)
):

    lat = None
    lng = None
    if propiedad.ubicacion_geografica:
        lat, lng = propiedad.ubicacion_geografica.split(",")
    point = None
    if lat and lng:
        point = f"POINT({float(lng)} {float(lat)})"

    query = text("""
        INSERT INTO propiedad (
            nombre_propiedad,
            descripcion,
            direccion,
            ubicacion_geografica,
            construccion_m2,
            terreno_m2,
            precio_original,
            tipo_moneda,
            url_imagen,
            precio_bob,
            precio_usd,
            cambio_utilizado,
            precio_m2_bob,
            precio_m2_usd,
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
            :url_imagen,
            :precio_bob,
            :precio_usd,
            :cambio_utilizado,
            :precio_m2_bob,
            :precio_m2_usd,
            :id_zona,
            :id_tipo_propiedad
        )
    """)

    db.execute(query, {
        "nombre_propiedad": propiedad.nombre_propiedad,
        "descripcion": propiedad.descripcion,
        "direccion": propiedad.direccion,
        "point": point,
        "construccion_m2": propiedad.construccion_m2,
        "terreno_m2": propiedad.terreno_m2,
        "precio_original": propiedad.precio_original,
        "tipo_moneda": propiedad.tipo_moneda,
        "url_imagen": propiedad.url_imagen,
        "precio_bob": propiedad.precio_bob,
        "precio_usd": propiedad.precio_usd,
        "cambio_utilizado": propiedad.cambio_utilizado,
        "precio_m2_bob": propiedad.precio_m2_bob,
        "precio_m2_usd": propiedad.precio_m2_usd,
        "id_zona": propiedad.id_zona,
        "id_tipo_propiedad": propiedad.id_tipo_propiedad
    })

    db.commit()

    return {
        "message": "Propiedad guardada correctamente"
    }
    
    
    


@property_router.post("/remax-sync")
async def sync_propiedades_remax(
    db: Session = Depends(get_db)
):

    url = "https://remax.bo/api/search/terreno/cochabamba"

    params = {
        "order[]": [1, 3],
        "page": 1,
        "swLat": -17.49804427435114,
        "swLng": -66.37390136718751,
        "neLat": -17.31393222192294,
        "neLng": -65.96809387207033
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        result = response.json()

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
            url_imagen,
            precio_bob,
            precio_usd,
            cambio_utilizado,
            precio_m2_bob,
            precio_m2_usd,
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
            :url_imagen,
            :precio_bob,
            :precio_usd,
            :cambio_utilizado,
            :precio_m2_bob,
            :precio_m2_usd,
            :id_zona,
            :id_tipo_propiedad
        )
    """)

    total_insertadas = 0

    for item in result.get("data", []):

        if item.get("transaction_type", {}).get("name") != "Venta":
            continue

        slug = item.get("slug")
        descripcion = item.get("listing_information", {}).get("subtype_property", {}).get("name")
        direccion = item.get("location", {}).get("first_address")
        url_imagen = item.get("default_imagen", {}).get("url")

        latitud = item.get("location", {}).get("latitude")
        longitud = item.get("location", {}).get("longitude")

        point = None
        if latitud and longitud:
            point = f"POINT({float(longitud)} {float(latitud)})"

        terreno_m2 = Decimal(item.get("listing_information", {}).get("land_m2", 0)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        precio_original = Decimal(item.get("price", {}).get("amount", 0)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        db.execute(insert_query, {
            "nombre_propiedad": slug,
            "descripcion": descripcion,
            "direccion": direccion,
            "point": point,
            "construccion_m2": Decimal(0),
            "terreno_m2": terreno_m2,
            "precio_original": precio_original,
            "tipo_moneda": "BOB",
            "url_imagen": url_imagen,
            "precio_bob": precio_original,
            "precio_usd": None,
            "cambio_utilizado": Decimal("6.86"),
            "precio_m2_bob": None,
            "precio_m2_usd": None,
            "id_zona": 1,
            "id_tipo_propiedad": 1
        })

        total_insertadas += 1

    db.commit()

    return {
        "message": "Propiedades guardadas correctamente",
        "total_insertadas": total_insertadas
    }