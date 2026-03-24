from typing import Optional
from pydantic import BaseModel
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

    latitud: Optional[float] = None
    longitud: Optional[float] = None
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
    
    

class RequestKriging(BaseModel):
    punto: PuntoSeleccionado
    propiedades: List[Propiedad_Encontrada]