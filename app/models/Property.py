from pydantic import BaseModel, Field
from typing import Optional


class PropiedadBase(BaseModel):
    nombre_propiedad: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None

class PropiedadCreate(PropiedadBase):
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    construccion_m2: float = 0
    terreno_m2: float

    precio_original: float
    tipo_moneda: str = Field(..., pattern="^(BOB|USD)$")

    id_zona: int
    id_tipo_propiedad: int