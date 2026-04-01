from fastapi import APIRouter, Depends
import httpx
from decimal import Decimal, ROUND_HALF_UP
from app.models.Property import PropiedadBase
from app.db.supabase import *
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio

c21_router = APIRouter(prefix="/c21", tags=["Propiedades C21"])
    
    
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




@c21_router.get("/count-all")
async def count_all_properties():
    url = "https://c21.com.bo/v/resultados/tipo_casa-o-casa-en-condominio-o-departamento-o-penthouse-o-terreno-o-quinta-o-rural-o-rancho-o-cochera-o-edificio-o-colegio-o-hotel-o-proyecto-o-local-o-oficinas-o-deposito-o-tinglado-o-ganaderas-o-agricolas/operacion_venta/en-pais_bolivia/ordenado-por_fecha-de-alta_ascendente/pagina_1/por_Cochabamba?json=true"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0"
        })

        data = response.json()

        total = int(data.get("totalHits", 0))

    return {
        "total_properties": total
    }





@c21_router.post("/post")
async def sync_propiedades_century21(
    db: Session = Depends(get_db)
):

    base_url = "https://c21.com.bo/v/resultados/tipo_casa-o-casa-en-condominio-o-departamento-o-penthouse-o-terreno-o-quinta-o-rural-o-rancho-o-cochera-o-edificio-o-colegio-o-hotel-o-proyecto-o-local-o-oficinas-o-deposito-o-tinglado-o-ganaderas-o-agricolas/operacion_venta/en-pais_bolivia/ordenado-por_fecha-de-alta_descendiente/pagina_{page}/por_Cochabamba"

    total_insertadas = 0
    page = 1
    max_pages = 100

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

        while page <= max_pages:

            url = base_url.format(page=page)

            response = await client.get(
                url,
                params={"json": "true"},
                headers={"User-Agent": "Mozilla/5.0"}
            )

            data = response.json()
            propiedades = data.get("results", [])

            if not propiedades:
                break

            for item in propiedades:

                encabezado = item.get("encabezado")
                calle = item.get("calle")
                municipio = item.get("municipio")
                tipo_propiedad_api = item.get("tipoPropiedad")

                nombre_propiedad = f"{encabezado} {calle}"

                # 📍 GEO
                lat = item.get("lat")
                lon = item.get("lon")

                point = None
                if lat and lon:
                    point = f"POINT({float(lon)} {float(lat)})"

                # 📐 METROS
                terreno_m2 = Decimal(
                    item.get("m2T") or 0
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                construccion_m2 = Decimal(
                    item.get("m2C") or 0
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # 💰 PRECIO (USD)
                precio = Decimal(
                    item.get("precios", {})
                    .get("vista", {})
                    .get("precio", 0)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # 🖼️ IMAGEN
                fotos = item.get("fotos", {}).get("propiedadThumbnail", [])
                url_imagen = fotos[0] if fotos else None

                # -----------------------------
                # 🔹 ZONA
                # -----------------------------
                id_zona = None

                if municipio:
                    zona_result = db.execute(text("""
                        SELECT id_zona FROM zona
                        WHERE LOWER(nombre_zona) = LOWER(:nombre)
                    """), {"nombre": municipio}).fetchone()

                    if zona_result:
                        id_zona = zona_result[0]
                    else:
                        id_zona = db.execute(text("""
                            INSERT INTO zona (nombre_zona)
                            VALUES (:nombre)
                            RETURNING id_zona
                        """), {"nombre": municipio}).fetchone()[0]
                        db.commit()

                # -----------------------------
                # 🔹 TIPO PROPIEDAD
                # -----------------------------
                id_tipo_propiedad = None

                if tipo_propiedad_api:
                    tipo_result = db.execute(text("""
                        SELECT id_tipo_propiedad
                        FROM tipo_propiedad
                        WHERE LOWER(nombre_tipo_propiedad) = LOWER(:nombre)
                    """), {"nombre": tipo_propiedad_api}).fetchone()

                    if tipo_result:
                        id_tipo_propiedad = tipo_result[0]
                    else:
                        id_tipo_propiedad = db.execute(text("""
                            INSERT INTO tipo_propiedad (nombre_tipo_propiedad)
                            VALUES (:nombre)
                            RETURNING id_tipo_propiedad
                        """), {"nombre": tipo_propiedad_api}).fetchone()[0]
                        db.commit()

                if not id_tipo_propiedad:
                    id_tipo_propiedad = 30  # Otros

                if not id_zona:
                    continue

                # -----------------------------
                # INSERT
                # -----------------------------
                db.execute(insert_query, {
                    "nombre_propiedad": nombre_propiedad,
                    "descripcion": None,
                    "direccion": calle,
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
            await asyncio.sleep(0.4)

    return {
        "message": "Century21 sincronizado correctamente",
        "total_insertadas": total_insertadas
    }