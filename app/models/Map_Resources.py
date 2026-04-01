from pydantic import BaseModel
from typing import Optional
class TipoPropiedadResponse(BaseModel):
    id_tipo_propiedad: int
    nombre_tipo_propiedad: str
    
    
class Zona(BaseModel):
    id_zona: int
    nombre_zona: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None