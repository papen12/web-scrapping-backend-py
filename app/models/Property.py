from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from typing import List

class PropiedadBase(BaseModel):
    nombre_propiedad: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None

    latitud: Optional[float] = None
    longitud: Optional[float] = None

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




class PropiedadCreate(BaseModel):

    nombre_propiedad: str
    descripcion: Optional[str]
    direccion: Optional[str]

    latitud: float
    longitud: float

    construccion_m2: Decimal
    terreno_m2: Decimal

    precio_original: Decimal
    tipo_moneda: str
    cambio_utilizado: Decimal

    id_zona: int
    id_tipo_propiedad: int

class PropiedadResponse(PropiedadBase):
    id_propiedad: int

    class Config:
        from_attributes = True
        
        
class PropiedadUpdate(BaseModel):

    nombre_propiedad: str
    descripcion: Optional[str]
    direccion: Optional[str]

    construccion_m2: Decimal
    terreno_m2: Decimal

    precio_original: Decimal
    tipo_moneda: str
    cambio_utilizado: Decimal

    id_zona: int
    id_tipo_propiedad: int
    
    
class FiltroBusqueda(BaseModel):
    tipos: List[int]
    zonas: List[int]