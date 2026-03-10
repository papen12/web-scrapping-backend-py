from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class PropiedadBase(BaseModel):
    nombre_propiedad: str = Field(..., max_length=255)
    descripcion: Optional[str] = None
    direccion: Optional[str] = None
    ubicacion_geografica: Optional[str] = None

    construccion_m2: Decimal = Field(0, max_digits=10, decimal_places=2)
    terreno_m2: Decimal = Field(..., max_digits=10, decimal_places=2)
    
    url_imagen:Optional[str]=None

    precio_original: Decimal = Field(..., max_digits=12, decimal_places=2)
    tipo_moneda: str = Field(..., min_length=3, max_length=3)  # 'BOB' o 'USD'

    precio_bob: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    precio_usd: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)

    cambio_utilizado: Optional[Decimal] = Field(None, max_digits=10, decimal_places=4)
    precio_m2_bob: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    precio_m2_usd: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)

    id_zona: int
    id_tipo_propiedad: int