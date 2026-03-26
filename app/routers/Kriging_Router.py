from fastapi import APIRouter
from app.models.Kriging import RequestKriging
from pykrige.ok import OrdinaryKriging
import numpy as np
from pyproj import Transformer

kriging_router = APIRouter(prefix="/calculo", tags=["Calculo de kriging"])

@kriging_router.post("/estimar")
def calcular_punto(data: RequestKriging):

    lats = np.array([p.latitud for p in data.propiedades])
    lons = np.array([p.longitud for p in data.propiedades])
    valores = np.array([float(p.precio_m2_usd) for p in data.propiedades])

    valores = np.clip(
        valores,
        np.percentile(valores, 5),
        np.percentile(valores, 95)
    )

    valores_log = np.log(valores)

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32719", always_xy=True)

    x, y = transformer.transform(lons, lats)
    x_target, y_target = transformer.transform(
        data.punto.longitud,
        data.punto.latitud
    )

    distancias = np.sqrt((x - x_target) ** 2 + (y - y_target) ** 2)

    mask = distancias <= data.punto.radio

    x = x[mask]
    y = y[mask]
    valores_log = valores_log[mask]

    OK = OrdinaryKriging(
        x,
        y,
        valores_log,
        variogram_model="exponential",
        verbose=False,
        enable_plotting=False
    )

    z, ss = OK.execute("points", [x_target], [y_target])

    precio_estimado = float(np.exp(z[0]))

    return {
        "precio_m2_estimado": precio_estimado,
        "varianza_error": float(ss[0])
    }