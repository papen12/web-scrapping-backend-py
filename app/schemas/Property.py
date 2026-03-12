from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class PropiedadBase(BaseModel):
    nombre_propiedad: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None
    ubicacion_geografica: Optional[str] = None

    construccion_m2: Decimal
    terreno_m2: Decimal

    url_imagen: Optional[str] = None

    precio_original: Decimal
    tipo_moneda: str

    precio_bob: Optional[Decimal] = None
    precio_usd: Optional[Decimal] = None

    cambio_utilizado: Optional[Decimal] = None
    precio_m2_bob: Optional[Decimal] = None
    precio_m2_usd: Optional[Decimal] = None

    id_zona: int
    id_tipo_propiedad: int


class PropiedadResponse(PropiedadBase):
    id_propiedad: int

    class Config:
        from_attributes = True