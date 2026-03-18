from pydantic import BaseModel
from typing import Optional

class PuntoInteresBase(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    id_tipo_punto_interes: int


class PuntoInteresCreate(PuntoInteresBase):
    pass


class PuntoInteres(PuntoInteresBase):
    id_punto_interes: int


class PuntoSeleccionado(BaseModel):
    latitud: float
    longitud: float
    radio: int = 1000  
    
class PuntoEncontrado(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    tipoPuntoInteres:str