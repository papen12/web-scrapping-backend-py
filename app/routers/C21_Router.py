from fastapi import APIRouter, Depends
import httpx
from decimal import Decimal, ROUND_HALF_UP
from app.models.Property import PropiedadBase
from app.db.supabase import *
from sqlalchemy.orm import Session
from sqlalchemy import text


c21_router = APIRouter(prefix="/c21", tags=["Propiedades Remax"])
    
    
@c21_router.get("/ver")
async def get_propiedades_century21(
    db: Session = Depends(get_db)
):

    url = "https://c21.com.bo/v/resultados/tipo_terreno/operacion_venta/en-pais_bolivia/en-estado_cochabamba/moneda_usd/ordenado-por_fecha-de-alta_descendiente/por_Cochabamba"
    params = {"json": "true"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    propiedades_list = []

    for item in data.get("results", []):

        municipio = item.get("municipio")
        calle = item.get("calle")
        encabezado = item.get("encabezado")

        lat = item.get("lat")
        lon = item.get("lon")

        m2 = Decimal(item.get("m2T", 0)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        contrato = Decimal(
            item.get("precios", {})
            .get("contrato", {})
            .get("precio", 0)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        imagen = None
        fotos = item.get("fotos", {}).get("propiedadThumbnail", [])

        if fotos:
            imagen = fotos[0]


        zona_query = text("""
            SELECT id_zona
            FROM zona
            WHERE LOWER(nombre_zona) = LOWER(:municipio)
            LIMIT 1
        """)

        zona_result = db.execute(
            zona_query,
            {"municipio": municipio}
        ).fetchone()

        id_zona = zona_result[0] if zona_result else None


        propiedad = PropiedadBase(
            nombre_propiedad=f"{encabezado} {calle}",
            descripcion=None,
            direccion=calle,
            ubicacion_geografica=f"{lat},{lon}" if lat and lon else None,
            construccion_m2=Decimal(0),
            terreno_m2=m2,
            precio_original=contrato,
            tipo_moneda="BOB",
            url_imagen=imagen,
            precio_bob=None,
            precio_usd=None,
            cambio_utilizado=Decimal("6.96"),
            precio_m2_bob=None,
            precio_m2_usd=None,
            id_zona=id_zona,
            id_tipo_propiedad=1
        )

        propiedades_list.append(propiedad)

    return propiedades_list 








@c21_router.post("/post")
async def sync_propiedades_century21(
    db: Session = Depends(get_db)
):

    url = "https://c21.com.bo/v/resultados/tipo_terreno/operacion_venta/en-pais_bolivia/en-estado_cochabamba/moneda_usd/ordenado-por_fecha-de-alta_descendiente/por_Cochabamba"

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
        ON CONFLICT (nombre_propiedad) DO NOTHING
    """)

    params = {"json": "true"}

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.get(url, params=params)
        result = response.json()

        propiedades = result.get("results", [])

        for item in propiedades:

            encabezado = item.get("encabezado")
            calle = item.get("calle")
            municipio = item.get("municipio")

            nombre_propiedad = f"{encabezado} {calle}"

            lat = item.get("lat")
            lon = item.get("lon")

            point = None
            if lat and lon:
                point = f"POINT({float(lon)} {float(lat)})"

            terreno_m2 = Decimal(
                item.get("m2T", 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            precio_vista = Decimal(
                item.get("precios", {})
                .get("vista", {})
                .get("precio", 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            fotos = item.get("fotos", {}).get("propiedadThumbnail", [])
            url_imagen = fotos[0] if fotos else None
            id_zona = None

            if municipio:

                zona_query = text("""
                    SELECT id_zona
                    FROM zona
                    WHERE LOWER(nombre_zona) = LOWER(:nombre)
                """)

                zona_result = db.execute(
                    zona_query,
                    {"nombre": municipio}
                ).fetchone()

                if zona_result:
                    id_zona = zona_result[0]

                else:

                    insert_zona_query = text("""
                        INSERT INTO zona (nombre_zona)
                        VALUES (:nombre)
                        RETURNING id_zona
                    """)

                    id_zona = db.execute(
                        insert_zona_query,
                        {"nombre": municipio}
                    ).fetchone()[0]

                    db.commit()
            db.execute(insert_query, {
                "nombre_propiedad": nombre_propiedad,
                "descripcion": None,
                "direccion": calle,
                "point": point,
                "construccion_m2": Decimal(0),
                "terreno_m2": terreno_m2,
                "precio_original": precio_vista,
                "tipo_moneda": "BOB",
                "url_imagen": url_imagen,
                "precio_bob": precio_vista,
                "precio_usd": None,
                "cambio_utilizado": Decimal("6.96"),
                "precio_m2_bob": None,
                "precio_m2_usd": None,
                "id_zona": id_zona,
                "id_tipo_propiedad": 1
            })

            total_insertadas += 1

        db.commit()

    return {
        "message": "Century21 sincronizado",
        "total_insertadas": total_insertadas
    }