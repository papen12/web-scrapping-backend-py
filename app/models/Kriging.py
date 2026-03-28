from typing import Optional
from pydantic import BaseModel,Field
from decimal import Decimal
from typing import List

class PuntoSeleccionado(BaseModel):
    latitud: float
    longitud: float
    radio: int = 1000  
    

class Propiedad_Encontrada(BaseModel):
    id_propiedad: int
    nombre_propiedad: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None

    latitud: float
    longitud: float
    distancia_metros: Optional[float] = None

    construccion_m2: Optional[Decimal] = None 
    terreno_m2: Decimal

    precio_bob: Optional[Decimal] = None
    precio_usd: Optional[Decimal] = None
    cambio_utilizado: Optional[Decimal] = None
    precio_m2_bob: Optional[Decimal] = None
    precio_m2_usd: Optional[Decimal] = None

    id_zona: int
    id_tipo_propiedad: int
    
    
class PropiedadKriging(BaseModel):
    id_propiedad: int
    latitud: float
    longitud: float
    precio_m2_usd: Decimal = Field(gt=0)
    id_zona: int
    id_tipo_propiedad: int
    terreno_m2: Optional[Decimal] = None
    distancia_metros: Optional[float] = None
class RequestKriging(BaseModel):
    punto: PuntoSeleccionado
    propiedades: List[PropiedadKriging]