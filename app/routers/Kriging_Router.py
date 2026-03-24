from fastapi import APIRouter
from typing import List
from app.models.Kriging import RequestKriging
from pykrige.ok import OrdinaryKriging
import numpy as np

kriging_router = APIRouter(prefix="/calculo", tags=["Calculo de kriging"])

@kriging_router.post("/estimar")
def calcular_punto(data: RequestKriging):

    props_validas = [
        p for p in data.propiedades
        if p.precio_m2_usd is not None and p.latitud and p.longitud
    ]

    if len(props_validas) < 3:
        return {"error": "No hay suficientes datos"}
    lats = np.array([p.latitud for p in props_validas])
    lons = np.array([p.longitud for p in props_validas])
    valores = np.array([float(p.precio_m2_usd) for p in props_validas])

    OK = OrdinaryKriging(
        lons,
        lats,
        valores,
        variogram_model='linear',
        verbose=False,
        enable_plotting=False
    )

    z, ss = OK.execute(
        'points',
        [data.punto.longitud],
        [data.punto.latitud]
    )

    return {
        "precio_m2_estimado": float(z[0]),
        "confianza": float(ss[0])
    }