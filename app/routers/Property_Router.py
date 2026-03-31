from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.supabase import get_db
from app.models.Property import PropiedadCreate,PropiedadResponse,PropiedadUpdate,FiltroBusqueda
from typing import List
from app.models.Kriging import Propiedad_Encontrada,PuntoSeleccionado

property_router = APIRouter(prefix="/propiedades", tags=["Propiedades"])

@property_router.get("/", response_model=list[PropiedadResponse])
def getproperties(db: Session = Depends(get_db)):

    query = text("SELECT * FROM obtener_propiedades()")

    result = db.execute(query)
    propiedades = result.mappings().all()

    return propiedades

@property_router.get("/mapa/{id_tipo}", response_model=List[PropiedadResponse])
def obtener_propiedades_mapa(id_tipo: int, db: Session = Depends(get_db)):

    query = text("SELECT * FROM filtro_tipo_propiedad(:id_tipo)")

    result = db.execute(query, {"id_tipo": id_tipo})
    propiedades = result.mappings().all()

    return propiedades



@property_router.get("/{propiedad_id}", response_model=PropiedadResponse)
def obtener_propiedad(propiedad_id: int, db: Session = Depends(get_db)):

    query = text("""
        SELECT * 
        FROM public.obtener_propiedad_por_id(:id)
    """)

    result = db.execute(query, {"id": propiedad_id})
    propiedad = result.mappings().first()

    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return propiedad

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
@property_router.put("/{propiedad_id}")
def editar_propiedad_api(
    propiedad_id: int,
    propiedad: PropiedadUpdate,
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT editar_propiedad(
            :id_propiedad,
            :nombre,
            :descripcion,
            :direccion,
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
        "id_propiedad": propiedad_id,
        "nombre": propiedad.nombre_propiedad,
        "descripcion": propiedad.descripcion,
        "direccion": propiedad.direccion,
        "construccion": propiedad.construccion_m2,
        "terreno": propiedad.terreno_m2,
        "precio": propiedad.precio_original,
        "moneda": propiedad.tipo_moneda,
        "cambio": propiedad.cambio_utilizado,
        "zona": propiedad.id_zona,
        "tipo": propiedad.id_tipo_propiedad
    })

    db.commit()

    id_editado = result.scalar()

    if not id_editado:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return {
        "mensaje": "Propiedad actualizada correctamente",
        "id_propiedad": id_editado
    }
    
    

@property_router.delete("/{propiedad_id}")
def eliminar_propiedad_api(propiedad_id: int, db: Session = Depends(get_db)):

    query = text("""
        SELECT eliminar_propiedad(:id_propiedad)
    """)

    result = db.execute(query, {
        "id_propiedad": propiedad_id
    })

    db.commit()

    id_eliminado = result.scalar()

    if not id_eliminado:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return {
        "mensaje": "Propiedad eliminada correctamente",
        "id_propiedad": id_eliminado
    }
    
@property_router.post("/filtrar-tipos", response_model=list[PropiedadResponse])
def filtrar_propiedades_por_tipo(
    tipos: List[int],
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT * 
        FROM public.obtener_propiedades_por_tipos(:tipos)
    """)

    result = db.execute(query, {"tipos": tipos})
    propiedades = result.mappings().all()

    return propiedades

@property_router.post("/filtrar-zonas", response_model=list[PropiedadResponse])
def filtrar_propiedades_por_zonas(
    zonas: List[int],
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT *
        FROM public.obtener_propiedades_por_zonas(:zonas)
    """)

    result = db.execute(query, {"zonas": zonas})
    propiedades = result.mappings().all()

    return propiedades



@property_router.post("/buscar", response_model=list[PropiedadResponse])
def buscar_propiedades(filtro: FiltroBusqueda, db: Session = Depends(get_db)):

    query = text("""
        SELECT *
        FROM public.obtener_propiedades_por_tipo_zona(:tipos, :zonas)
    """)

    result = db.execute(query, {
        "tipos": filtro.tipos,
        "zonas": filtro.zonas
    })

    propiedades = result.mappings().all()

    return propiedades


@property_router.post("/cercanas", response_model=list[Propiedad_Encontrada])
def PropiedadesCercanas(punto_seleccionado: PuntoSeleccionado, db: Session = Depends(get_db)):
    query = text("""
        SELECT *
        FROM public.propiedades_cercanas(:lat, :lon, :radio)
    """)
    
    result = db.execute(query, {
        "lat": punto_seleccionado.latitud,
        "lon": punto_seleccionado.longitud,
        "radio": punto_seleccionado.radio
    })
    propiedades = [dict(row) for row in result.mappings().all()]

    return propiedades