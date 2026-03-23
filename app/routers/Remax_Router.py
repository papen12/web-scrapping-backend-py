from fastapi import APIRouter, Depends
import httpx
from decimal import Decimal, ROUND_HALF_UP
from app.models.Property import PropiedadBase
from app.db.supabase import *
from sqlalchemy.orm import Session
from sqlalchemy import text


remax_router=APIRouter(prefix="/remax")

@remax_router.get("/ver")
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






@remax_router.post("/post")
async def sync_propiedades_remax(
    db: Session = Depends(get_db)
):

    url = "https://remax.bo/api/search/terreno/cochabamba"

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

    async with httpx.AsyncClient(timeout=30) as client:

        while True:

            params = {
                "order[]": [1, 3],
                "page": page,
                "swLat": -17.49804427435114,
                "swLng": -66.37390136718751,
                "neLat": -17.31393222192294,
                "neLng": -65.96809387207033
            }

            response = await client.get(url, params=params)
            result = response.json()

            propiedades = result.get("data", [])
            if not propiedades:
                break

            for item in propiedades:

                if item.get("transaction_type", {}).get("name") != "Venta":
                    continue

                slug = item.get("slug")

                descripcion = item.get(
                    "listing_information", {}
                ).get("subtype_property", {}).get("name")

                direccion = item.get(
                    "location", {}
                ).get("first_address")

                url_imagen = item.get(
                    "default_imagen", {}
                ).get("url")

                latitud = item.get(
                    "location", {}
                ).get("latitude")

                longitud = item.get(
                    "location", {}
                ).get("longitude")

                point = None
                if latitud and longitud:
                    point = f"POINT({float(longitud)} {float(latitud)})"

                terreno_m2 = Decimal(
                    item.get("listing_information", {}).get("land_m2", 0)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                precio_original = Decimal(
                    item.get("price", {}).get("amount", 0)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                nombre_zona = item.get(
                    "location", {}
                ).get("zone", {}).get("name")

                id_zona = None

                if nombre_zona:

                    zona_query = text("""
                        SELECT id_zona
                        FROM zona
                        WHERE nombre_zona = :nombre
                    """)

                    zona_result = db.execute(
                        zona_query,
                        {"nombre": nombre_zona}
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
                            {"nombre": nombre_zona}
                        ).fetchone()[0]

                        db.commit()

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
                    "id_zona": id_zona,
                    "id_tipo_propiedad": 1
                })

                total_insertadas += 1

            db.commit()

            print(f"Página {page} procesada")

            page += 1

    return {
        "message": "Sincronización completada",
        "total_insertadas": total_insertadas,
        "paginas_recorridas": page - 1
    }
    
    
    
    





@remax_router.get("/contar-terrenos")
async def count_propiedades_por_zona():

    url = "https://remax.bo/api/search/terreno/cochabamba/tiquipaya"

    params = {
        "order[]": [1, 3],
        "page": 1,
       "swLat": -58.63121664342478,
    "swLng": -113.20312500000001,
    "neLat": 25.16517336866393,
    "neLng": 94.57031250000001
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        result = response.json()

    zonas_count = {}

    for item in result.get("data", []):

        if item.get("transaction_type", {}).get("name") != "Venta":
            continue

        zona = item.get("location", {}).get("zone", {}).get("name")

        if not zona:
            zona = "Sin zona"

        if zona not in zonas_count:
            zonas_count[zona] = 0

        zonas_count[zona] += 1

    return zonas_count












@remax_router.post("/post-tiquipaya")
async def sync_propiedades_tiquipaya(
    db: Session = Depends(get_db)
):

    url = "https://remax.bo/api/search/terreno/cochabamba/tiquipaya"

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

    async with httpx.AsyncClient(timeout=30) as client:

        while True:

            params = {
                "order[]": [1, 3],
                "page": page
            }

            response = await client.get(url, params=params)
            result = response.json()

            propiedades = result.get("data", [])

            if not propiedades:
                break

            for item in propiedades:

                # SOLO ventas
                if item.get("transaction_type", {}).get("name") != "Venta":
                    continue

                # SOLO zona TIQUIPAYA
                zona_nombre = item.get("location", {}).get("zone", {}).get("name")

                if not zona_nombre or zona_nombre.lower() != "tiquipaya":
                    continue

                slug = item.get("slug")

                descripcion = item.get(
                    "listing_information", {}
                ).get("subtype_property", {}).get("name")

                direccion = item.get(
                    "location", {}
                ).get("first_address")

                url_imagen = item.get(
                    "default_imagen", {}
                ).get("url")

                latitud = item.get("location", {}).get("latitude")
                longitud = item.get("location", {}).get("longitude")

                point = None
                if latitud and longitud:
                    point = f"POINT({float(longitud)} {float(latitud)})"

                terreno_m2 = Decimal(
                    item.get("listing_information", {}).get("land_m2", 0)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                precio_original = Decimal(
                    item.get("price", {}).get("amount", 0)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                # buscar zona
                zona_query = text("""
                    SELECT id_zona
                    FROM zona
                    WHERE nombre_zona = :nombre
                """)

                zona_result = db.execute(
                    zona_query,
                    {"nombre": zona_nombre}
                ).fetchone()

                if zona_result:
                    id_zona = zona_result[0]
                else:

                    insert_zona = text("""
                        INSERT INTO zona (nombre_zona)
                        VALUES (:nombre)
                        RETURNING id_zona
                    """)

                    id_zona = db.execute(
                        insert_zona,
                        {"nombre": zona_nombre}
                    ).fetchone()[0]

                    db.commit()

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
                    "id_zona": id_zona,
                    "id_tipo_propiedad": 1
                })

                total_insertadas += 1

            db.commit()

            print(f"Página {page} procesada")
            page += 1

    return {
        "message": "Propiedades de Tiquipaya sincronizadas",
        "total_insertadas": total_insertadas,
        "paginas_recorridas": page - 1
    }
    
    
    
    


@remax_router.post("/post-colcapirhua")
async def sync_casas_colcapirhua(
    db: Session = Depends(get_db)
):

    url = "https://remax.bo/api/search/casa/cochabamba/colcapirhua"

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

    params = {
        "order[]": [1, 3],
        "page": 1,
        "swLat": -17.470537548710915,
        "swLng": -66.43844604492189,
        "neLat": -17.286397793949188,
        "neLng": -66.03195190429689
    }

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.get(url, params=params)
        result = response.json()

        propiedades = result.get("data", [])

        for item in propiedades:

            if item.get("transaction_type", {}).get("name") != "Venta":
                continue

            listing = item.get("listing_information") or {}
            location = item.get("location") or {}
            price = item.get("price") or {}
            default_imagen = item.get("default_imagen") or {}

            slug = item.get("slug")

            descripcion = listing.get("subtype_property", {}).get("name")

            direccion = location.get("first_address")

            url_imagen = default_imagen.get("url")

            latitud = location.get("latitude")
            longitud = location.get("longitude")

            point = None
            if latitud and longitud:
                point = f"POINT({float(longitud)} {float(latitud)})"

            construccion_m2 = Decimal(
                listing.get("construction_area_m", 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            terreno_m2 = Decimal(
                listing.get("land_m2", 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            precio_original = Decimal(
                price.get("amount", 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            precio_usd = Decimal(
                price.get("price_in_dollars", 0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            db.execute(insert_query, {
                "nombre_propiedad": slug,
                "descripcion": descripcion,
                "direccion": direccion,
                "point": point,
                "construccion_m2": construccion_m2,
                "terreno_m2": terreno_m2,
                "precio_original": precio_original,
                "tipo_moneda": "BOB",
                "url_imagen": url_imagen,
                "precio_bob": precio_original,
                "precio_usd": precio_usd,
                "cambio_utilizado": Decimal("6.86"),
                "precio_m2_bob": None,
                "precio_m2_usd": None,
                "id_zona": 6,
                "id_tipo_propiedad": 2
            })

            total_insertadas += 1

        db.commit()

    return {
        "message": "Casas de Colcapirhua sincronizadas",
        "total_insertadas": total_insertadas
    }